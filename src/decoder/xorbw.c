#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
int main(){ int T=1024, N=4064; uint64_t **a=malloc(N*sizeof(void*)); for(int i=0;i<N;i++){a[i]=aligned_alloc(64,T); for(int j=0;j<T/8;j++)a[i][j]=i*j;}
 struct timespec t0,t1; clock_gettime(CLOCK_MONOTONIC,&t0); long ops=0;
 for(int rep=0;rep<50;rep++) for(int i=1;i<N;i++){ for(int j=0;j<T/8;j++) a[i][j]^=a[(i*7)%N][j]; ops++; }
 clock_gettime(CLOCK_MONOTONIC,&t1); double dt=(t1.tv_sec-t0.tv_sec)+(t1.tv_nsec-t0.tv_nsec)*1e-9;
 printf("XOR de pacotes de 1 KB nesta máquina: %.1f GB/s (%ld XORs em %.3f s)\n", ops*(double)T/1e9/dt, ops, dt); return 0;}
