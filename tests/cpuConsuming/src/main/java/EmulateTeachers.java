import com.github.javafaker.Faker;
import com.mongodb.MongoClient;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.MongoDatabase;
import com.mongodb.client.model.IndexOptions;
import org.bson.Document;
import java.lang.Thread;
import io.github.cdimascio.dotenv.Dotenv;

class Database {
    static Dotenv dotenv = Dotenv.configure().ignoreIfMissing().load();
    static MongoClient mongo = new MongoClient(dotenv.get("MONGODB_HOST"));
    static MongoDatabase database = mongo.getDatabase(dotenv.get("DB"));
    static MongoCollection<Document> school = database.getCollection("school");

    public static Document giveRandomStudent(){
        Faker faker = new Faker();

        String name = faker.name().fullName();
        String address = faker.address().streetAddress();
        int marks = faker.number().numberBetween(1, 100);

        return new Document("name", name)
                .append("address", address)
                .append("marks", marks);
    }

    public static int findCountOfStudentsWithMarks(int marks) {
        Document query = new Document("marks", marks);
        return (int) school.count(query);
    }

    public static void giveBonusMarks(int marks) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", 5));
        school.updateMany(query, update);
    }

    public static void takeAwayMarks(int marks) {
        Document query = new Document("marks", marks);
        Document update = new Document("$inc", new Document("marks", -5));
        school.updateMany(query, update);
    }
}

class DBQueryRunnable implements Runnable {
    public void run(){
        for (int i = 0; i < 5000; i++) {
            int marks = (int) (Math.random() * 100);
            int count = Database.findCountOfStudentsWithMarks(marks);

            if (count > 0 && marks <= 95) {
                Database.giveBonusMarks(marks);
            }
        }

        for (int i = 0; i < 5000; i++) {
            int marks = (int) (Math.random() * 100);
            int count = Database.findCountOfStudentsWithMarks(marks);

            if (count > 0 && marks >= 5) {
                Database.takeAwayMarks(marks);
            }
        }
    }
}

class TeacherStatusRunnable implements Runnable{
    private String teacher;
    Thread dbQueryThread;

    TeacherStatusRunnable(String teacher, Thread dbQueryThread){
        this.teacher = teacher;
        this.dbQueryThread = dbQueryThread;
    }
    public void run(){
        while(dbQueryThread.isAlive()){
            System.out.println("Processing " + teacher + "'s request");
        }
    }
}

public class EmulateTeachers{
    static void checkConection(){
        System.out.println("Environment variables:");
        System.out.println("MONGODB_HOST: " + Database.dotenv.get("MONGODB_HOST"));
        System.out.println("DB: " + Database.dotenv.get("DB"));
        System.out.println("Number of documents in school collection: " + Database.school.count());
    }

    static void populateDB(){
        String db = Database.dotenv.get("DB");

        if (db.equals("schoolWithIndex")) {
            populateIndexedDB();
        } else if (db.equals("schoolWithoutIndex")) {
            populateNonIndexedDB();
        } else {
            System.out.println("Invalid DB name");
        }
    }

    static void populateIndexedDB(){
        IndexOptions indexOptions = new IndexOptions();
        Database.school.createIndex(new Document("marks", 1), indexOptions);

        for(int i = 0; i < 10000; i++){
            Database.school.insertOne(Database.giveRandomStudent());
        }
    }

    static void populateNonIndexedDB(){
        for(int i = 0; i < 10000; i++){
            Database.school.insertOne(Database.giveRandomStudent());
        }
    }

    static void emulateQueueOfTeachers() throws InterruptedException {
        while(true) {
            teacherQuery(new Faker().name().fullName());
            Thread.sleep(60000);
        }
    }

    static public void teacherQuery(String teacher) throws InterruptedException {
        Thread dbQueryThread = new Thread(new DBQueryRunnable());
        Thread teacherStatusThread = new Thread(new TeacherStatusRunnable(teacher, dbQueryThread));

        dbQueryThread.start();
        teacherStatusThread.start();
//        dbQueryThread.join();
//        System.out.println("Finished processing " + teacher + "'s request");
//        System.out.println("Current Time in human readable format: " + new java.util.Date());
    }

    public static void main(String args[]) throws InterruptedException {
//        checkConection();
//        populateDB();
        emulateQueueOfTeachers();
    }
}