#include<stdio.h>
void main()
{
int num1=0;
int num2=1;
int result=0;
int n=0;
int i=0;
printf("Enter the number of fibonacci terms ");
scanf("%d ",&n);
printf("%d ",num2);
while(i<n-1)
{

result=num1+num2;
printf("%d ",result);
i++;
num1=num2;
num2=result;
}
}









