"""Exercise the production flash-copy code with host partition/flash stubs."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CXX = os.environ.get('CXX') or shutil.which('g++')
if not CXX:
    raise SystemExit('Set CXX to a desktop g++ compiler.')

SDK = r'''
#pragma once
#include <stddef.h>
#include <stdint.h>
#define ESP_PARTITION_TYPE_DATA 1
#define ESP_PARTITION_TYPE_ANY 0xff
#define ESP_PARTITION_SUBTYPE_ANY 0xff
#define ESP_OK 0
typedef int esp_err_t;
typedef struct { uint8_t type,subtype; uint32_t address,size; char label[17]; } esp_partition_t;
typedef struct partition_iterator* esp_partition_iterator_t;
const esp_partition_t* esp_partition_find_first(int,int,const char*);
esp_partition_iterator_t esp_partition_find(int,int,const char*);
const esp_partition_t* esp_partition_get(esp_partition_iterator_t);
esp_partition_iterator_t esp_partition_next(esp_partition_iterator_t);
void esp_partition_iterator_release(esp_partition_iterator_t);
esp_err_t esp_partition_erase_range(const esp_partition_t*,size_t,size_t);
esp_err_t esp_partition_write(const esp_partition_t*,size_t,const void*,size_t);
int esp_vfs_spiffs_unregister(const char*);
'''

TEST = r'''
#include "esp_partition.h"
#include "rom_flash_io.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>
extern "C" bool gameStationIsCardenza() {
#ifdef TEST_CARDENZA
return true;
#else
return false;
#endif
}
struct partition_iterator { size_t n; };
static esp_partition_t rom={1,0x40,0x780000,0x80000,"cardenza_rom"};
static esp_partition_t app={0,0x12,0x400000,0x380000,"CardenzaTest"};
static esp_partition_t fs={1,0x82,0x390000,0x80000,"spiffs"};
static std::vector<const esp_partition_t*> rows;
static std::vector<unsigned char> flash;
static size_t erase_calls,write_calls,unmount_calls,erased,written;
static bool erase_fail,write_fail;
const esp_partition_t* esp_partition_find_first(int t,int,const char* name) {
  for(auto p:rows) if(p->type==t && !strcmp(p->label,name)) return p;
  return nullptr;
}
esp_partition_iterator_t esp_partition_find(int,int,const char*) {
  return rows.empty()?nullptr:new partition_iterator{0};
}
const esp_partition_t* esp_partition_get(esp_partition_iterator_t it) {return rows[it->n];}
esp_partition_iterator_t esp_partition_next(esp_partition_iterator_t it) {
  if(++it->n<rows.size()) return it;
  delete it; return nullptr;
}
void esp_partition_iterator_release(esp_partition_iterator_t it) {delete it;}
int esp_vfs_spiffs_unregister(const char*) {++unmount_calls;return 0;}
esp_err_t esp_partition_erase_range(const esp_partition_t* p,size_t off,size_t n) {
  ++erase_calls;assert(!off && n<=p->size && !(n&0xfff));erased=n;
  flash.assign(p->size,0xff);return erase_fail?-1:0;
}
esp_err_t esp_partition_write(const esp_partition_t* p,size_t off,const void* data,size_t n) {
  ++write_calls;assert(off==written && n<=8192 && off+n<=p->size);
  if(write_fail)return -1;
  memcpy(flash.data()+off,data,n);written+=n;return 0;
}
static void reset() {erase_calls=write_calls=unmount_calls=erased=written=0;erase_fail=write_fail=false;}
static void file(const char* path,size_t n) {
  FILE* f=fopen(path,"wb");assert(f);
  for(size_t i=0;i<n;++i) assert(fputc(i&255,f)!=EOF);
  fclose(f);
}
int main(int argc,char**argv) {
  assert(argc==2);const char* path=argv[1];
#ifdef TEST_CARDENZA
  rows={&app,&rom};reset();
  assert(findRomPartition(nullptr)==&rom);
  assert(!findRomPartition("spiffs") && !unmount_calls);
  assert(eraseRomPartition(&rom,1) && erased==65536);
  assert(eraseRomPartition(&rom,65536) && erased==65536);
  assert(eraseRomPartition(&rom,65537) && erased==131072);
  assert(eraseRomPartition(&rom,rom.size) && erased==rom.size);
  reset();assert(!eraseRomPartition(&rom,0));assert(!eraseRomPartition(&rom,rom.size+1));
  assert(!erase_calls && !write_calls);
  auto good=rom;
  for(int scenario=0;scenario<8;++scenario) {
    rom=good;
    if(scenario==0)rom.address=0x3f0000;
    if(scenario==1)rom.address=0x780001;
    if(scenario==2)rom.size=0x80001;
    if(scenario==3)rom.size=0;
    if(scenario==4)rom.size=0xffffffff;
    if(scenario==5)rom.type=0;
    if(scenario==6)rom.subtype=0x82;
    if(scenario==7)strcpy(rom.label,"spiffs");
    reset();assert(!findRomPartition(ROM_PARTITION_LABEL));
    assert(!eraseRomPartition(&rom,1));size_t n=99;
    assert(!copyFileToPartition(path,&rom,&n,nullptr,nullptr) && !n);
    assert(!erase_calls && !write_calls);
  }
  rom=good;app.size=0x381000;reset();
  assert(!findRomPartition(ROM_PARTITION_LABEL) && !eraseRomPartition(&rom,1));
  assert(!erase_calls);app.size=0x380000;
  rows={&app};assert(!eraseRomPartition(&rom,1));rows={&app,&rom};
  for(size_t length:{size_t(0),size_t(1),size_t(8193),size_t(65537),size_t(0x80000),size_t(0x80001)}) {
    file(path,length);reset();size_t n=99;
    bool success=copyFileToPartition(path,&rom,&n,nullptr,nullptr);
    assert(success==(length>0 && length<=rom.size));
    if(!success)assert(!erase_calls && !write_calls && !n);
    else {
      assert(n==length && written==length && erase_calls==1);
      assert(erased==((length+65535)&~size_t(65535)));
      for(size_t i=0;i<length;++i)assert(flash[i]==(i&255));
    }
  }
  file(path,8193);reset();erase_fail=true;size_t n=99;
  assert(!copyFileToPartition(path,&rom,&n,nullptr,nullptr) && !n && !write_calls);
  reset();write_fail=true;
  assert(!copyFileToPartition(path,&rom,&n,nullptr,nullptr) && !n && write_calls==1);
  puts("Cardenza: label/type/bounds/alignment/overlap guards, erase rounding, exact copy and failures PASS");
#else
  rows={&fs};reset();
  assert(findRomPartition(nullptr)==&fs && unmount_calls==1);
  file(path,8193);size_t n=0;
  assert(copyFileToPartition(path,&fs,&n,nullptr,nullptr) && n==8193 && erased==65536);
  puts("Original target: generic SPIFFS lookup and copy behavior PASS");
#endif
}
'''

with tempfile.TemporaryDirectory(prefix='cardenza-rom-') as tmp:
    out = Path(tmp)
    (out/'esp_partition.h').write_text(SDK, encoding='utf-8')
    (out/'esp_spi_flash.h').write_text('#include "esp_partition.h"\n', encoding='utf-8')
    (out/'test.cpp').write_text(TEST, encoding='utf-8')
    for cardenza in (True, False):
        exe = out/('cardenza.exe' if cardenza else 'original.exe')
        cmd = [CXX, '-std=c++11', '-Wno-unknown-pragmas', '-I'+str(out),
               '-I'+str(ROOT/'src/vfs'), str(ROOT/'src/vfs/rom_flash_io.c'),
               str(out/'test.cpp'), '-o', str(exe)]
        if cardenza:
            cmd.insert(1, '-DTEST_CARDENZA=1')
        subprocess.run(cmd, check=True)
        subprocess.run([str(exe), str(out/'synthetic.bin')], check=True)
