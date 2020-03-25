#include<stdio.h>
void main()
{
printf("Prefix example\n");
int a = 1;
int b=++a;
printf("a= %d\n",a);
printf("b= %d\n",b);

printf("Postfix example\n");
int d = 1;
int e = d++;   // d = 1
int f = d; 
printf("d= %d\n",d);
printf("e= %d\n",e);
printf("f= %d\n",f);
}









