import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Stage;

public class Main extends Application {
    @Override
    public void start(Stage primaryStage) {
        // Sidebar
        VBox sidebar = new VBox(15);
        sidebar.setPadding(new Insets(20));
        sidebar.setStyle("-fx-background-color: #2c3e50;");
        sidebar.setPrefWidth(200);

        Label appLabel = new Label("HMS");
        appLabel.setStyle("-fx-text-fill: white; -fx-font-size: 24px; -fx-font-weight: bold;");

        Button dashboardBtn = new Button("Dashboard");
        Button patientBtn = new Button("Patient Management");
        Button doctorBtn = new Button("Doctor / Staff");
        Button appointmentBtn = new Button("Appointments / OPD");
        Button billingBtn = new Button("Billing & Finance");
        Button labBtn = new Button("Lab Management");
        Button adminBtn = new Button("Admin Tools");

        for(Button btn : new Button[]{dashboardBtn, patientBtn, doctorBtn, appointmentBtn, billingBtn, labBtn, adminBtn}) {
            btn.setMaxWidth(Double.MAX_VALUE);
            btn.setStyle("-fx-background-color: transparent; -fx-text-fill: white; -fx-font-size: 14px;");
            btn.setAlignment(Pos.CENTER_LEFT);
        }

        sidebar.getChildren().addAll(appLabel, dashboardBtn, patientBtn, doctorBtn, appointmentBtn, billingBtn, labBtn, adminBtn);

        // Main Content
        VBox mainContent = new VBox(15);
        mainContent.setPadding(new Insets(30));
        mainContent.setStyle("-fx-background-color: #ecf0f1;");

        Label titleLabel = new Label("Patient Registration");
        titleLabel.setStyle("-fx-font-size: 22px; -fx-font-weight: bold; -fx-text-fill: #34495e;");

        GridPane formGrid = new GridPane();
        formGrid.setVgap(10);
        formGrid.setHgap(15);

        TextField nameField = new TextField();
        nameField.setPromptText("Name");
        TextField genderField = new TextField();
        genderField.setPromptText("Gender");
        TextField ageField = new TextField();
        ageField.setPromptText("Age");
        TextField funderField = new TextField();
        funderField.setPromptText("Funder");
        TextField contactField = new TextField();
        contactField.setPromptText("Contact (Phone, Email)");
        TextArea medicalHistory = new TextArea();
        medicalHistory.setPromptText("Medical History");
        medicalHistory.setPrefRowCount(3);

        formGrid.add(new Label("Name:"), 0,0);
        formGrid.add(nameField, 1,0);
        formGrid.add(new Label("Gender:"), 2,0);
        formGrid.add(genderField,3,0);

        formGrid.add(new Label("Age:"),0,1);
        formGrid.add(ageField,1,1);
        formGrid.add(new Label("Funder:"),2,1);
        formGrid.add(funderField,3,1);

        formGrid.add(new Label("Contact:"),0,2);
        formGrid.add(contactField,1,2,3,1);

        formGrid.add(new Label("Medical History:"),0,3);
        formGrid.add(medicalHistory,1,3,3,1);

        HBox buttonBox = new HBox(15);
        Button clearBtn = new Button("Clear Form");
        Button registerBtn = new Button("Register & Generate ID");
        clearBtn.setStyle("-fx-background-color: #95a5a6; -fx-text-fill: white;");
        registerBtn.setStyle("-fx-background-color: #27ae60; -fx-text-fill: white;");

        buttonBox.getChildren().addAll(clearBtn, registerBtn);

        mainContent.getChildren().addAll(titleLabel, formGrid, buttonBox);

        // Root layout
        HBox root = new HBox();
        root.getChildren().addAll(sidebar, mainContent);

        Scene scene = new Scene(root, 1000, 600);
        primaryStage.setScene(scene);
        primaryStage.setTitle("Hospital Management System");
        primaryStage.show();
    }

    public static void main(String[] args) {
        launch(args);
    }
}