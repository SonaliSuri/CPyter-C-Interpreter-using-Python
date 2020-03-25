#include<stdio.h>
int sum(int x,int y)
{
return (x+y);
}

void main()
{
int x=0;
int y=0;
int result=0;
printf("Enter the first number ");
scanf("%d",&x);
printf("Enter the second number ");
scanf("%d",&y);
result= sum(x,y);
printf("The sum of %d and %d is %d",x,y,result);
}





