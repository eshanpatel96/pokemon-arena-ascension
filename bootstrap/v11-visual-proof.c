/* Visual evidence runner, NOT a campaign pass. ROM remains unchanged.
 * Uses debugger writes solely to select existing maps/rank fixtures quickly.
 * Every pixel is then produced by the real GBA ROM running in mGBA.
 * Room entry, walk-up and A-button challenge are executed by native code.
 */
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include <mgba/core/log.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
struct Symbol { uint32_t a; char n[180]; };
static struct Symbol syms[100000]; static unsigned count;
static struct mCore *c; static color_t pixels[240*160];
static const char *out; static unsigned record,frameid;
static void quiet(struct mLogger*l,int category,enum mLogLevel level,const char*fmt,va_list args) { (void)l;(void)category;if(level==mLOG_FATAL){vfprintf(stderr,fmt,args);fputc('\n',stderr);} }
static struct mLogger logger={quiet,NULL};
static uint32_t sym(const char *n) { for(unsigned i=0;i<count;i++)if(!strcmp(n,syms[i].n))return syms[i].a;fprintf(stderr,"Missing %s\n",n);exit(3); }
static uint32_t r8(uint32_t a){return c->busRead8(c,a);} static uint32_t r16(uint32_t a){return c->busRead16(c,a);} static uint32_t r32(uint32_t a){return c->busRead32(c,a);}
static void w8(uint32_t a,uint8_t v){c->busWrite8(c,a,v);} static void w16(uint32_t a,uint16_t v){c->busWrite16(c,a,v);} static void w32(uint32_t a,uint32_t v){c->busWrite32(c,a,v);}
static void ppm(const char*n){char p[1024];snprintf(p,sizeof(p),"%s/%s.ppm",out,n);FILE*f=fopen(p,"wb");if(!f){perror(p);exit(3);}fprintf(f,"P6\n240 160\n255\n");for(unsigned i=0;i<240*160;i++){unsigned v=pixels[i];unsigned char rgb[]={v&255,(v>>8)&255,(v>>16)&255};fwrite(rgb,1,3,f);}fclose(f);}
static void frames(unsigned n,unsigned keys){c->setKeys(c,keys);for(unsigned i=0;i<n;i++){c->runFrame(c);if(record&&!(frameid++%4)){char name[80];snprintf(name,sizeof(name),"clip/frame-%06u",frameid/4);ppm(name);}}c->setKeys(c,0);}
static void press(unsigned k){frames(2,k);frames(38,0);}
static void snap(const char*n){ppm(n);uint32_t sb=r32(sym("gSaveBlock1Ptr"));printf("CAPTURE %s native_frame=%u callback=%08x map=%u,%u pos=%d,%d layout=%u\n",n,c->frameCounter(c),r32(sym("gMain")+4),r8(sb+4),r8(sb+5),(int16_t)r16(sb),(int16_t)r16(sb+2),r16(sb+0x32));fflush(stdout);}
static void setvar(unsigned id,unsigned val){w16(r32(sym("gSaveBlock1Ptr"))+0x139c+2*(id-0x4000),val);}
static void warp(unsigned map,unsigned x,unsigned y,unsigned rank,unsigned floor){
 setvar(0x40fa,rank);setvar(0x40fb,floor);setvar(0x40fc,1);
 uint32_t w=sym("sWarpDestination");w8(w,26);w8(w+1,map);w8(w+2,255);w8(w+3,0);w16(w+4,x);w16(w+6,y);
 w32(sym("gFieldCallback"),sym("FieldCB_WarpExitFadeFromBlack")|1);
 w32(sym("gMain")+4,sym("WarpIntoMap")|1);frames(1,0);
 w32(sym("gMain")+4,sym("CB2_LoadMap")|1);frames(240,0);
 printf("DEBUG_FIXTURE existing map 26,%u rank=%u floor=%u via native WarpIntoMap; NOT a earned progression test\n",map,rank,floor);
}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"usage: proof ROM symbols output\n");return 2;}out=argv[3];mkdir(out,0777);char path[1024];snprintf(path,sizeof(path),"%s/clip",out);mkdir(path,0777);
 FILE*f=fopen(argv[2],"r");if(!f)return 2;char line[512],t,n[180];unsigned a;while(fgets(line,sizeof(line),f)){if(sscanf(line,"%x %c %179s",&a,&t,n)==3&&a>=0x02000000&&a<0x0a000000&&t!='a'&&t!='A'&&count<100000){syms[count].a=a;strcpy(syms[count++].n,n);}}fclose(f);
 mLogSetDefaultLogger(&logger);c=mCoreFind(argv[1]);if(!c||!c->init(c))return 2;mCoreInitConfig(c,NULL);struct mCoreOptions opts={0};opts.useBios=false;opts.skipBios=true;opts.audioBuffers=1024;opts.sampleRate=32768;opts.mute=true;opts.logLevel=0;mCoreConfigLoadDefaults(&c->config,&opts);mCoreLoadConfig(c);c->setVideoBuffer(c,pixels,240);if(!mCoreLoadFile(c,argv[1]))return 2;c->reset(c);
 frames(300,0);snap("00-title");press(8);frames(150,0);snap("01-native-menu");press(1);frames(480,0);snap("02-city");
 uint32_t sb=r32(sym("gSaveBlock1Ptr"));if(r8(sb+4)!=26||r8(sb+5)!=89){fprintf(stderr,"fresh start did not reach city\n");return 4;}
 size_t sz=c->stateSize(c);void*base=malloc(sz);if(!base||!c->saveState(c,base))return 5;
 const char*names[]={"03-bronze","04-gale","05-verdant","06-phantom","07-inferno","08-tidal","09-thunder","10-astral","11-champion","12-elite-articuno","13-elite-registeel","14-elite-raikou","15-elite-regice"};
 unsigned maps[]={114,115,116,117,118,119,120,121,122,123,124,125,126};unsigned floors[]={3,4,4,5,5,6,7,8,4,0,1,2,3};
 for(unsigned i=0;i<13;i++){if(!c->loadState(c,base))return 5;warp(maps[i],9,10,i<9?i:8,floors[i]);snap(names[i]);char view[120];snprintf(view,sizeof(view),"%s-north",names[i]);frames(64,64);frames(30,0);snap(view);}
 c->loadState(c,base);warp(92,5,6,0,0);snap("16-trial-room");
 c->loadState(c,base);warp(114,9,18,0,3);snap("17-bronze-entry");record=1;frames(35,0);frames(208,64);frames(30,0);snap("18-bronze-walk-up");press(1);frames(120,0);snap("19-bronze-dialogue");press(1);frames(100,0);press(1);frames(100,0);snap("20-bronze-confirm");press(1);frames(300,0);snap("21-battle-or-staging");
 frames(300,0);snap("22-native-battle");
 for(unsigned i=0;i<6;i++){press(1);frames(10,0);}snap("23-native-attacks");
 frames(80,64);press(1);frames(80,16);press(1);frames(80,128);press(1);frames(80,32);press(1);frames(60,0);snap("24-native-movement");record=0;
 free(base);mCoreConfigDeinit(&c->config);c->deinit(c);printf("COMPLETE: real framebuffer captures, debug room fixtures. No full campaign/save/Delta acceptance claimed.\n");return 0;
}
