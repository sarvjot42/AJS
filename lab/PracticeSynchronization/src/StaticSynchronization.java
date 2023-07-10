class TableA
{
    synchronized static void printTable(int n){
        for(int i=1;i<=10;i++){
            System.out.println(n*i);
            try{
                Thread.sleep(400);
            }catch(Exception e){}
        }
    }
}
class MyThread1A extends Thread{
    public void run(){
        TableA.printTable(1);
    }
}
class MyThread2A extends Thread{
    public void run(){
        TableA.printTable(10);
    }
}
class MyThread3 extends Thread{
    public void run(){
        TableA.printTable(100);
    }
}
class MyThread4 extends Thread{
    public void run(){
        TableA.printTable(1000);
    }
}
public class StaticSynchronization{
    public static void main(String t[]){
        MyThread1A t1=new MyThread1A();
        MyThread2A t2=new MyThread2A();
        MyThread3 t3=new MyThread3();
        MyThread4 t4=new MyThread4();
        t1.start();
        t2.start();
        t3.start();
        t4.start();
    }
}    