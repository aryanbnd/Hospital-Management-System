import json
import os
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from dataclasses import dataclass, field
from typing import List, Union
import pandas as pd
from datetime import datetime
import logging
import base64  

logging.basicConfig(filename='hospital_management.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ==================== DATA MODELS ====================

@dataclass
class Bill:
    id: int
    amount: float
    description: str
    date: str
    status: str = "Pending"  # Pending / Paid

    def to_dict(self):
        return {
            'id': self.id, 'amount': self.amount, 'description': self.description,
            'date': self.date, 'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Prescription:
    id: int
    medicine: str
    description: str
    date: str
    image_base64: str = ""  # Base64 encoded image data (optional)

    def to_dict(self):
        return {
            'id': self.id, 'medicine': self.medicine, 'description': self.description,
            'date': self.date, 'image_base64': self.image_base64
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Patient:
    id: int
    name: str
    age: int
    ailment: str
    password: str
    reports: List[str] = field(default_factory=list)
    bills: List[Bill] = field(default_factory=list)
    prescriptions: List[Prescription] = field(default_factory=list)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'age': self.age, 'ailment': self.ailment,
            'password': self.password, 'reports': self.reports,
            'bills': [b.to_dict() for b in self.bills],
            'prescriptions': [p.to_dict() for p in self.prescriptions]
        }

    @classmethod
    def from_dict(cls, data):
        bills_data = data.get('bills', [])
        # Handle legacy string bills
        if bills_data and isinstance(bills_data[0], str):
            converted = []
            for i, old in enumerate(bills_data, 1):
                try:
                    parts = old.rsplit(' ', 1)
                    if len(parts) == 2 and parts[1].replace('.', '', 1).isdigit():
                        desc, amt = parts[0].strip(), float(parts[1])
                    else:
                        desc, amt = old, 0.0
                    converted.append(Bill(i, amt, desc, "2025-01-01", "Pending"))
                except:
                    converted.append(Bill(i, 0.0, old, "2025-01-01", "Pending"))
            bills = converted
        else:
            bills = [Bill.from_dict(b) for b in bills_data]

        prescriptions = [Prescription.from_dict(p) for p in data.get('prescriptions', [])]

        return cls(
            data['id'], data['name'], data['age'], data['ailment'],
            data['password'], data.get('reports', []), bills, prescriptions
        )

@dataclass
class Doctor:
    id: int
    name: str
    specialization: str
    password: str

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'specialization': self.specialization, 'password': self.password}

    @classmethod
    def from_dict(cls, data):
        return cls(data['id'], data['name'], data['specialization'], data['password'])

@dataclass
class Appointment:
    id: int
    patient_id: int
    doctor_id: int
    date: str
    time: str

    def to_dict(self):
        return {'id': self.id, 'patient_id': self.patient_id, 'doctor_id': self.doctor_id, 'date': self.date, 'time': self.time}

    @classmethod
    def from_dict(cls, data):
        return cls(data['id'], data['patient_id'], data['doctor_id'], data['date'], data['time'])

# ==================== DATA STORAGE ====================

# Use Pandas DataFrames for data management to enable easier querying, analysis, and export
patients_df: pd.DataFrame = pd.DataFrame(columns=['id', 'name', 'age', 'ailment', 'password', 'reports', 'bills', 'prescriptions'])
doctors_df: pd.DataFrame = pd.DataFrame(columns=['id', 'name', 'specialization', 'password'])
appointments_df: pd.DataFrame = pd.DataFrame(columns=['id', 'patient_id', 'doctor_id', 'date', 'time'])

PATIENTS_FILE = 'patients.json'
DOCTORS_FILE = 'doctors.json'
APPOINTMENTS_FILE = 'appointments.json'

def load_data():
    global patients_df, doctors_df, appointments_df

    if os.path.exists(PATIENTS_FILE):
        with open(PATIENTS_FILE, 'r') as f:
            data = json.load(f)
            patients_list = [Patient.from_dict(p) for p in data]
            patients_df = pd.DataFrame([p.to_dict() for p in patients_list])

    for path, df_name, cls in [
        (DOCTORS_FILE, 'doctors_df', Doctor),
        (APPOINTMENTS_FILE, 'appointments_df', Appointment)
    ]:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                items = [cls.from_dict(item) for item in data]
                globals()[df_name] = pd.DataFrame([item.to_dict() for item in items])

    logging.info("Data loaded successfully.")

def save_data():
    for path, df in [
        (PATIENTS_FILE, patients_df),
        (DOCTORS_FILE, doctors_df),
        (APPOINTMENTS_FILE, appointments_df)
    ]:
        with open(path, 'w') as f:
            json.dump(df.to_dict(orient='records'), f, indent=4)

    logging.info("Data saved successfully.")

def get_next_id(df: pd.DataFrame, id_col: str = 'id') -> int:
    """Auto-generate next ID for DataFrames."""
    if df.empty:
        return 1
    return df[id_col].max() + 1

# ==================== MAIN GUI ====================

class HospitalManagementSystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hospital Management System")
        self.geometry("1100x750")
        self.configure(bg="#f1f5f9")
        self.current_user = None
        self.role = None
        self.current_bill_patient = None
        self.current_prescription_patient = None
        load_data()
        self.show_login()

        # Apply a modern theme for better design
        style = ttk.Style(self)
        style.theme_use('clam')  # Use a cleaner theme
        style.configure('Treeview', background='#ffffff', fieldbackground='#ffffff', font=('Arial', 10))
        style.configure('Treeview.Heading', font=('Arial', 11, 'bold'))

    def show_login(self):
        self.clear_window()
        tk.Label(self, text="Hospital Management System", font=("Helvetica", 26, "bold"),
                 bg="#f1f5f9", fg="#1e293b").pack(pady=40)

        frame = tk.Frame(self, bg="#ffffff", bd=2, relief="groove")
        frame.pack(pady=20, padx=80, ipadx=50, ipady=40)

        tk.Label(frame, text="User ID", bg="#ffffff", font=("Arial", 12)).grid(row=0, column=0, padx=20, pady=15, sticky="e")
        self.id_entry = tk.Entry(frame, width=30, font=("Arial", 12))
        self.id_entry.grid(row=0, column=1, pady=15)

        tk.Label(frame, text="Password", bg="#ffffff", font=("Arial", 12)).grid(row=1, column=0, padx=20, pady=15, sticky="e")
        self.pass_entry = tk.Entry(frame, show="*", width=30, font=("Arial", 12))
        self.pass_entry.grid(row=1, column=1, pady=15)

        tk.Label(frame, text="Login as", bg="#ffffff", font=("Arial", 12)).grid(row=2, column=0, padx=20, pady=15, sticky="e")
        self.role_var = tk.StringVar(value="Patient")
        tk.Radiobutton(frame, text="Patient", variable=self.role_var, value="Patient", bg="#ffffff").grid(row=2, column=1, sticky="w", padx=30)
        tk.Radiobutton(frame, text="Doctor", variable=self.role_var, value="Doctor", bg="#ffffff").grid(row=2, column=1, sticky="e", padx=30)

        tk.Button(self, text="LOGIN", command=self.login,
                  bg="#2563eb", fg="white", font=("Arial", 14, "bold"),
                  width=15, relief="flat", pady=10).pack(pady=25)

    def login(self):
        try:
            uid = int(self.id_entry.get().strip())
            pw = self.pass_entry.get().strip()
            role = self.role_var.get()

            user = None
            if role == "Patient":
                mask = (patients_df['id'] == uid) & (patients_df['password'] == pw)
                if not patients_df[mask].empty:
                    user_dict = patients_df[mask].iloc[0].to_dict()
                    user = Patient.from_dict(user_dict)
            else:
                mask = (doctors_df['id'] == uid) & (doctors_df['password'] == pw)
                if not doctors_df[mask].empty:
                    user_dict = doctors_df[mask].iloc[0].to_dict()
                    user = Doctor.from_dict(user_dict)

            if user:
                self.current_user = user
                self.role = role
                logging.info(f"User {user.id} ({role}) logged in.")
                if role == "Patient":
                    self.show_patient_dashboard()
                else:
                    self.show_doctor_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials.")
        except ValueError:
            messagebox.showerror("Error", "ID must be a number.")
        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            messagebox.showerror("Error", "An unexpected error occurred.")

    def show_patient_dashboard(self):
        self.clear_window()
        tk.Label(self, text=f"Welcome, {self.current_user.name}", font=("Helvetica", 20, "bold"),
                 bg="#f1f5f9", fg="#1e293b").pack(pady=20)

        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=30, expand=True, fill="both")

        # Appointments Tab
        apps_tab = ttk.Frame(notebook)
        notebook.add(apps_tab, text="Appointments")

        tk.Label(apps_tab, text="Your Appointments", font=("Arial", 14, "bold"), bg="#f1f5f9").pack(pady=8)
        app_tree = ttk.Treeview(apps_tab, columns=("ID", "Doctor", "Date", "Time"), show="headings", height=6)
        app_tree.heading("ID", text="ID")
        app_tree.heading("Doctor", text="Doctor ID")
        app_tree.heading("Date", text="Date")
        app_tree.heading("Time", text="Time")

        patient_apps = appointments_df[appointments_df['patient_id'] == self.current_user.id]
        for _, app in patient_apps.iterrows():
            app_tree.insert("", "end", values=(app['id'], app['doctor_id'], app['date'], app['time']))
        app_tree.pack(pady=10, padx=50, fill="x")

        # Bills Tab
        bills_tab = ttk.Frame(notebook)
        notebook.add(bills_tab, text="Bills & Payments")

        tk.Label(bills_tab, text="Your Bills & Payments", font=("Arial", 14, "bold"), bg="#f1f5f9").pack(pady=15)

        columns = ("ID", "Date", "Description", "Amount", "Status")
        bill_tree = ttk.Treeview(bills_tab, columns=columns, show="headings", height=8)
        for col, txt in zip(columns, ["ID", "Date", "Description", "Amount", "Status"]):
            bill_tree.heading(col, text=txt)
            bill_tree.column(col, width=160 if col != "Description" else 240)

        # Get patient's bills
        patient_row = patients_df[patients_df['id'] == self.current_user.id].iloc[0]
        bills = patient_row['bills']  # List of dicts

        bills_df = pd.DataFrame(bills) if bills else pd.DataFrame(columns=['id', 'date', 'description', 'amount', 'status'])
        total_due = bills_df[bills_df['status'] == 'Pending']['amount'].sum() if not bills_df.empty else 0.0

        for _, bill in bills_df.iterrows():
            tag = "paid" if bill['status'] == "Paid" else "pending"
            bill_tree.insert("", "end", values=(
                bill['id'], bill['date'], bill['description'], f"Rs. {bill['amount']:,.2f}", bill['status']
            ), tags=(tag,))

        bill_tree.tag_configure("pending", foreground="#dc2626", font=("Arial", 10, "bold"))
        bill_tree.tag_configure("paid", foreground="#16a34a")
        bill_tree.pack(pady=10, padx=50, fill="x")

        tk.Label(bills_tab, text=f"Total Amount Due: Rs. {total_due:,.2f}",
                 font=("Arial", 14, "bold"), fg="#b91c1c" if total_due > 0 else "#15803d",
                 bg="#f1f5f9").pack(pady=10)

        # Prescriptions Tab
        prescriptions_tab = ttk.Frame(notebook)
        notebook.add(prescriptions_tab, text="Prescriptions")

        tk.Label(prescriptions_tab, text="Your Prescriptions", font=("Arial", 14, "bold"), bg="#f1f5f9").pack(pady=8)
        presc_tree = ttk.Treeview(prescriptions_tab, columns=("ID", "Medicine", "Description", "Date", "Image"), show="headings", height=8)
        presc_tree.heading("ID", text="ID")
        presc_tree.heading("Medicine", text="Medicine")
        presc_tree.heading("Description", text="Description")
        presc_tree.heading("Date", text="Date")
        presc_tree.heading("Image", text="Has Image")

        prescriptions = patient_row['prescriptions']  # List of dicts
        presc_df = pd.DataFrame(prescriptions) if prescriptions else pd.DataFrame()
        for _, presc in presc_df.iterrows():
            has_image = "Yes" if presc['image_base64'] else "No"
            presc_tree.insert("", "end", values=(presc['id'], presc['medicine'], presc['description'], presc['date'], has_image))

        presc_tree.pack(pady=10, padx=50, fill="x")

        # View Image Button
        def view_selected_image():
            sel = presc_tree.selection()
            if not sel:
                return
            pid = int(presc_tree.item(sel[0])["values"][0])
            presc_dict = next((p for p in prescriptions if p['id'] == pid), None)
            if presc_dict and presc_dict['image_base64']:
                image_data = base64.b64decode(presc_dict['image_base64'])
                image_popup = tk.Toplevel(self)
                image_popup.title("Prescription Image")
                img = tk.PhotoImage(data=image_data)
                tk.Label(image_popup, image=img).pack()
                image_popup.image = img  # Keep reference
            else:
                messagebox.showinfo("No Image", "No image available for this prescription.")

        tk.Button(prescriptions_tab, text="View Image", command=view_selected_image,
                  bg="#3b82f6", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(pady=10)

        tk.Button(self, text="LOGOUT", command=self.show_login,
                  bg="#ef4444", fg="white", font=("Arial", 12, "bold"),
                  width=15).pack(pady=20)

    def show_doctor_dashboard(self):
        self.clear_window()
        tk.Label(self, text=f"Doctor Panel • {self.current_user.name}", font=("Helvetica", 20, "bold"),
                 bg="#f1f5f9", fg="#1e293b").pack(pady=20)

        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, padx=30, expand=True, fill="both")

        # Patients Tab
        patients_tab = ttk.Frame(notebook)
        notebook.add(patients_tab, text="Patients")

        patient_tree = ttk.Treeview(patients_tab, columns=("ID", "Name", "Age", "Ailment"), show="headings", height=10)
        for col, txt in zip(("ID", "Name", "Age", "Ailment"), ("ID", "Name", "Age", "Ailment")):
            patient_tree.heading(col, text=txt)
            patient_tree.column(col, width=180 if col != "Name" else 280)

        patient_tree.pack(pady=10, padx=20, fill="both", expand=True)
        for _, p in patients_df.iterrows():
            patient_tree.insert("", "end", values=(p['id'], p['name'], p['age'], p['ailment']))

        tk.Button(patients_tab, text="Add New Patient", command=self.add_patient,
                  bg="#10b981", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(side="left", padx=10, pady=10)
        tk.Button(patients_tab, text="Change Patient Password", command=self.change_patient_password,
                  bg="#8b5cf6", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(side="left", padx=10, pady=10)
        tk.Button(patients_tab, text="Export Patients to CSV", command=self.export_patients_csv,
                  bg="#3b82f6", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(side="left", padx=10, pady=10)

        # Appointments Tab
        apps_tab = ttk.Frame(notebook)
        notebook.add(apps_tab, text="Appointments")

        app_tree = ttk.Treeview(apps_tab, columns=("ID", "Patient", "Date", "Time"), show="headings", height=10)
        for col, txt in zip(("ID", "Patient", "Date", "Time"), ("ID", "Patient", "Date", "Time")):
            app_tree.heading(col, text=txt)
            app_tree.column(col, width=180 if col != "Patient" else 280)

        app_tree.pack(pady=10, padx=20, fill="both", expand=True)
        for _, a in appointments_df.iterrows():
            patient_name = patients_df[patients_df['id'] == a['patient_id']]['name'].values[0] if not patients_df[patients_df['id'] == a['patient_id']].empty else f"ID {a['patient_id']}"
            app_tree.insert("", "end", values=(a['id'], f"{a['patient_id']} - {patient_name}", a['date'], a['time']))

        tk.Button(apps_tab, text="Schedule New Appointment", command=self.schedule_appointment,
                  bg="#3b82f6", fg="white", font=("Arial", 11, "bold"), relief="flat").pack(pady=10)

        # Billing Tab
        billing_tab = ttk.Frame(notebook)
        notebook.add(billing_tab, text="Billing 💳")

        tk.Label(billing_tab, text="Patient Billing Management", font=("Helvetica", 16, "bold"),
                 bg="#1e40af", fg="white", pady=12).pack(fill="x")

        search_frame = tk.Frame(billing_tab, bg="#eff6ff")
        search_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(search_frame, text="Patient ID/Name:", bg="#eff6ff", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        self.bill_patient_search = tk.Entry(search_frame, width=40)
        self.bill_patient_search.pack(side="left", padx=10)

        tk.Button(search_frame, text="Load", command=self.load_patient_bills,
                  bg="#3b82f6", fg="white", relief="flat").pack(side="left")

        self.bill_patient_info = tk.Label(billing_tab, text="Select a patient", font=("Arial", 12),
                                         bg="white", fg="#64748b", pady=15, relief="ridge", bd=1)
        self.bill_patient_info.pack(fill="x", padx=20, pady=10)

        bill_tree_columns = ("ID", "Date", "Description", "Amount", "Status")
        self.bill_tree = ttk.Treeview(billing_tab, columns=bill_tree_columns, show="headings", height=10)
        for col, txt in zip(bill_tree_columns, ["ID", "Date", "Description", "Amount (NPR)", "Status"]):
            self.bill_tree.heading(col, text=txt)
            self.bill_tree.column(col, width=160 if col != "Description" else 250)

        self.bill_tree.pack(fill="both", expand=True, padx=20, pady=10)

        btn_frame = tk.Frame(billing_tab, bg="#f8fafc")
        btn_frame.pack(fill="x", padx=20, pady=15)

        tk.Button(btn_frame, text="Add Bill", command=self.add_new_bill,
                  bg="#10b981", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(btn_frame, text="Mark Paid", command=self.mark_bill_paid,
                  bg="#8b5cf6", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(btn_frame, text="Delete", command=self.delete_bill,
                  bg="#ef4444", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(btn_frame, text="Export Bills to CSV", command=self.export_bills_csv,
                  bg="#3b82f6", fg="white", relief="flat").pack(side="left", padx=8)

        # Prescriptions Tab
        prescriptions_tab = ttk.Frame(notebook)
        notebook.add(prescriptions_tab, text="Prescriptions 💊")

        tk.Label(prescriptions_tab, text="Patient Prescription Management", font=("Helvetica", 16, "bold"),
                 bg="#1e40af", fg="white", pady=12).pack(fill="x")

        presc_search_frame = tk.Frame(prescriptions_tab, bg="#eff6ff")
        presc_search_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(presc_search_frame, text="Patient ID/Name:", bg="#eff6ff", font=("Arial", 11, "bold")).pack(side="left", padx=10)
        self.presc_patient_search = tk.Entry(presc_search_frame, width=40)
        self.presc_patient_search.pack(side="left", padx=10)

        tk.Button(presc_search_frame, text="Load", command=self.load_patient_prescriptions,
                  bg="#3b82f6", fg="white", relief="flat").pack(side="left")

        self.presc_patient_info = tk.Label(prescriptions_tab, text="Select a patient", font=("Arial", 12),
                                          bg="white", fg="#64748b", pady=15, relief="ridge", bd=1)
        self.presc_patient_info.pack(fill="x", padx=20, pady=10)

        presc_tree_columns = ("ID", "Medicine", "Description", "Date", "Image")
        self.presc_tree = ttk.Treeview(prescriptions_tab, columns=presc_tree_columns, show="headings", height=10)
        for col, txt in zip(presc_tree_columns, ["ID", "Medicine", "Description", "Date", "Has Image"]):
            self.presc_tree.heading(col, text=txt)
            self.presc_tree.column(col, width=160 if col != "Description" else 250)

        self.presc_tree.pack(fill="both", expand=True, padx=20, pady=10)

        presc_btn_frame = tk.Frame(prescriptions_tab, bg="#f8fafc")
        presc_btn_frame.pack(fill="x", padx=20, pady=15)

        tk.Button(presc_btn_frame, text="Add Prescription", command=self.add_new_prescription,
                  bg="#10b981", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(presc_btn_frame, text="Delete", command=self.delete_prescription,
                  bg="#ef4444", fg="white", relief="flat").pack(side="left", padx=8)
        tk.Button(presc_btn_frame, text="View Image", command=self.view_prescription_image,
                  bg="#3b82f6", fg="white", relief="flat").pack(side="left", padx=8)

        tk.Button(self, text="LOGOUT", command=self.show_login,
                  bg="#ef4444", fg="white", font=("Arial", 12, "bold"), width=15).pack(pady=20)

    def load_patient_bills(self):
        search = self.bill_patient_search.get().strip().lower()
        if not search:
            messagebox.showwarning("Input Required", "Enter Patient ID or Name")
            return

        mask = patients_df['id'].astype(str).str.contains(search) | patients_df['name'].str.lower().str.contains(search)
        found_df = patients_df[mask]
        if found_df.empty:
            messagebox.showerror("Not Found", "Patient not found")
            return

        found = Patient.from_dict(found_df.iloc[0].to_dict())
        self.current_bill_patient = found
        self.bill_patient_info.config(text=f"Patient: {found.name} (ID: {found.id})", fg="#1e40af", bg="#dbeafe")

        self.bill_tree.delete(*self.bill_tree.get_children())
        bills = found.bills
        bills_df = pd.DataFrame([b.to_dict() for b in bills]) if bills else pd.DataFrame()
        total = bills_df[bills_df['status'] == 'Pending']['amount'].sum() if not bills_df.empty else 0.0

        for _, b in bills_df.iterrows():
            tag = "paid" if b['status'] == "Paid" else "pending"
            self.bill_tree.insert("", "end", values=(
                b['id'], b['date'], b['description'], f"Rs. {b['amount']:,.2f}", b['status']
            ), tags=(tag,))

        self.bill_tree.tag_configure("pending", foreground="#dc2626", font=("Arial", 10, "bold"))
        self.bill_tree.tag_configure("paid", foreground="#16a34a")

        # Update total due label (create if not exists)
        if hasattr(self, 'total_due_label'):
            self.total_due_label.config(text=f"Total Due: Rs. {total:,.2f}", fg="#b91c1c" if total > 0 else "#15803d")
        else:
            self.total_due_label = tk.Label(self.bill_patient_info.master,
                                            text=f"Total Due: Rs. {total:,.2f}",
                                            font=("Arial", 13, "bold"), fg="#b91c1c" if total > 0 else "#15803d",
                                            bg="#f8fafc")
            self.total_due_label.pack(pady=10)

    def add_new_bill(self):
        if not hasattr(self, 'current_bill_patient') or not self.current_bill_patient:
            messagebox.showwarning("No Patient", "Please select patient first")
            return

        popup = tk.Toplevel(self)
        popup.title("Add New Bill")
        popup.geometry("480x420")
        popup.configure(bg="#f8fafc")

        tk.Label(popup, text="New Bill", font=("Helvetica", 16, "bold"), bg="#1e40af", fg="white", pady=10).pack(fill="x")

        fields = [("Date (YYYY-MM-DD):", "date"),
                  ("Description:", "description"), ("Amount (NPR):", "amount")]

        entries = {}
        for label, key in fields:
            f = tk.Frame(popup, bg="#f8fafc")
            f.pack(fill="x", padx=30, pady=10)
            tk.Label(f, text=label, width=18, anchor="e", bg="#f8fafc").pack(side="left")
            entries[key] = tk.Entry(f, width=35)
            entries[key].pack(side="left", padx=10)

        # Auto-generate Bill ID
        patient_idx = patients_df[patients_df['id'] == self.current_bill_patient.id].index[0]
        current_bills = patients_df.at[patient_idx, 'bills']
        bid = get_next_id(pd.DataFrame(current_bills), 'id') if current_bills else 1
        tk.Label(popup, text=f"Bill ID: {bid} (Auto-generated)", bg="#f8fafc", font=("Arial", 12)).pack(pady=10)

        def save():
            try:
                amount = float(entries["amount"].get())
                date = entries["date"].get() or datetime.now().strftime("%Y-%m-%d")
                new_bill = Bill(bid, amount, entries["description"].get(), date)
                current_bills.append(new_bill.to_dict())
                patients_df.at[patient_idx, 'bills'] = current_bills
                save_data()
                logging.info(f"New bill {bid} added for patient {self.current_bill_patient.id}")
                messagebox.showinfo("Success", "Bill added!")
                popup.destroy()
                self.load_patient_bills()
            except Exception as e:
                logging.error(f"Add bill error: {str(e)}")
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Save Bill", command=save,
                  bg="#10b981", fg="white", font=("Arial", 12, "bold")).pack(pady=25)

    def mark_bill_paid(self):
        sel = self.bill_tree.selection()
        if not sel:
            return
        bid = int(self.bill_tree.item(sel[0])["values"][0])
        patient_idx = patients_df[patients_df['id'] == self.current_bill_patient.id].index[0]
        bills = patients_df.at[patient_idx, 'bills']
        for b in bills:
            if b['id'] == bid:
                b['status'] = "Paid"
                break
        patients_df.at[patient_idx, 'bills'] = bills
        save_data()
        logging.info(f"Bill {bid} marked paid for patient {self.current_bill_patient.id}")
        self.load_patient_bills()
        messagebox.showinfo("Success", "Marked as Paid")

    def delete_bill(self):
        sel = self.bill_tree.selection()
        if not sel or not messagebox.askyesno("Confirm", "Delete this bill?"):
            return
        bid = int(self.bill_tree.item(sel[0])["values"][0])
        patient_idx = patients_df[patients_df['id'] == self.current_bill_patient.id].index[0]
        bills = patients_df.at[patient_idx, 'bills']
        bills = [b for b in bills if b['id'] != bid]
        patients_df.at[patient_idx, 'bills'] = bills
        save_data()
        logging.info(f"Bill {bid} deleted for patient {self.current_bill_patient.id}")
        self.load_patient_bills()

    def load_patient_prescriptions(self):
        search = self.presc_patient_search.get().strip().lower()
        if not search:
            messagebox.showwarning("Input Required", "Enter Patient ID or Name")
            return

        mask = patients_df['id'].astype(str).str.contains(search) | patients_df['name'].str.lower().str.contains(search)
        found_df = patients_df[mask]
        if found_df.empty:
            messagebox.showerror("Not Found", "Patient not found")
            return

        found = Patient.from_dict(found_df.iloc[0].to_dict())
        self.current_prescription_patient = found
        self.presc_patient_info.config(text=f"Patient: {found.name} (ID: {found.id})", fg="#1e40af", bg="#dbeafe")

        self.presc_tree.delete(*self.presc_tree.get_children())
        prescriptions = found.prescriptions
        presc_df = pd.DataFrame([p.to_dict() for p in prescriptions]) if prescriptions else pd.DataFrame()

        for _, p in presc_df.iterrows():
            has_image = "Yes" if p['image_base64'] else "No"
            self.presc_tree.insert("", "end", values=(
                p['id'], p['medicine'], p['description'], p['date'], has_image
            ))

    def add_new_prescription(self):
        if not hasattr(self, 'current_prescription_patient') or not self.current_prescription_patient:
            messagebox.showwarning("No Patient", "Please select patient first")
            return

        popup = tk.Toplevel(self)
        popup.title("Add New Prescription")
        popup.geometry("500x500")
        popup.configure(bg="#f8fafc")

        tk.Label(popup, text="New Prescription", font=("Helvetica", 16, "bold"), bg="#1e40af", fg="white", pady=10).pack(fill="x")

        fields = [("Medicine:", "medicine"),
                  ("Description:", "description"),
                  ("Date (YYYY-MM-DD):", "date")]

        entries = {}
        for label, key in fields:
            f = tk.Frame(popup, bg="#f8fafc")
            f.pack(fill="x", padx=30, pady=10)
            tk.Label(f, text=label, width=18, anchor="e", bg="#f8fafc").pack(side="left")
            entries[key] = tk.Entry(f, width=35)
            entries[key].pack(side="left", padx=10)

        # Image Upload
        image_base64 = [""]
        tk.Label(popup, text="Upload Image (optional):", bg="#f8fafc").pack(pady=5)
        def upload_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
            if file_path:
                with open(file_path, "rb") as img_file:
                    image_base64[0] = base64.b64encode(img_file.read()).decode('utf-8')
                messagebox.showinfo("Success", "Image uploaded!")

        tk.Button(popup, text="Upload", command=upload_image, bg="#3b82f6", fg="white").pack(pady=5)

        # Auto-generate Prescription ID
        patient_idx = patients_df[patients_df['id'] == self.current_prescription_patient.id].index[0]
        current_prescriptions = patients_df.at[patient_idx, 'prescriptions']
        pid = get_next_id(pd.DataFrame(current_prescriptions), 'id') if current_prescriptions else 1
        tk.Label(popup, text=f"Prescription ID: {pid} (Auto-generated)", bg="#f8fafc", font=("Arial", 12)).pack(pady=10)

        def save():
            try:
                medicine = entries["medicine"].get()
                description = entries["description"].get()
                date = entries["date"].get() or datetime.now().strftime("%Y-%m-%d")
                new_presc = Prescription(pid, medicine, description, date, image_base64[0])
                current_prescriptions.append(new_presc.to_dict())
                patients_df.at[patient_idx, 'prescriptions'] = current_prescriptions
                save_data()
                logging.info(f"New prescription {pid} added for patient {self.current_prescription_patient.id}")
                messagebox.showinfo("Success", "Prescription added!")
                popup.destroy()
                self.load_patient_prescriptions()
            except Exception as e:
                logging.error(f"Add prescription error: {str(e)}")
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Save Prescription", command=save,
                  bg="#10b981", fg="white", font=("Arial", 12, "bold")).pack(pady=25)

    def delete_prescription(self):
        sel = self.presc_tree.selection()
        if not sel or not messagebox.askyesno("Confirm", "Delete this prescription?"):
            return
        pid = int(self.presc_tree.item(sel[0])["values"][0])
        patient_idx = patients_df[patients_df['id'] == self.current_prescription_patient.id].index[0]
        prescriptions = patients_df.at[patient_idx, 'prescriptions']
        prescriptions = [p for p in prescriptions if p['id'] != pid]
        patients_df.at[patient_idx, 'prescriptions'] = prescriptions
        save_data()
        logging.info(f"Prescription {pid} deleted for patient {self.current_prescription_patient.id}")
        self.load_patient_prescriptions()

    def view_prescription_image(self):
        sel = self.presc_tree.selection()
        if not sel:
            return
        pid = int(self.presc_tree.item(sel[0])["values"][0])
        patient_idx = patients_df[patients_df['id'] == self.current_prescription_patient.id].index[0]
        prescriptions = patients_df.at[patient_idx, 'prescriptions']
        presc_dict = next((p for p in prescriptions if p['id'] == pid), None)
        if presc_dict and presc_dict['image_base64']:
            image_data = base64.b64decode(presc_dict['image_base64'])
            image_popup = tk.Toplevel(self)
            image_popup.title("Prescription Image")
            img = tk.PhotoImage(data=image_data)
            tk.Label(image_popup, image=img).pack()
            image_popup.image = img  # Keep reference
        else:
            messagebox.showinfo("No Image", "No image available for this prescription.")

    def change_patient_password(self):
        popup = tk.Toplevel(self)
        popup.title("Change Patient Password")
        popup.geometry("450x350")
        popup.configure(bg="#f8fafc")

        tk.Label(popup, text="Change Patient Password", font=("Helvetica", 16, "bold"), bg="#1e40af", fg="white", pady=10).pack(fill="x")

        tk.Label(popup, text="Patient ID:", bg="#f8fafc").pack(pady=5)
        patient_id_entry = tk.Entry(popup, width=40)
        patient_id_entry.pack(pady=5)

        tk.Label(popup, text="New Password:", bg="#f8fafc").pack(pady=5)
        new_pass_entry = tk.Entry(popup, show="*", width=40)
        new_pass_entry.pack(pady=5)

        tk.Label(popup, text="Confirm New Password:", bg="#f8fafc").pack(pady=5)
        confirm_pass_entry = tk.Entry(popup, show="*", width=40)
        confirm_pass_entry.pack(pady=5)

        # Doctor's password for authorization
        tk.Label(popup, text="Your Doctor Password (for authorization):", bg="#f8fafc").pack(pady=5)
        doctor_pass_entry = tk.Entry(popup, show="*", width=40)
        doctor_pass_entry.pack(pady=5)

        def save():
            try:
                pid = int(patient_id_entry.get())
                new_pw = new_pass_entry.get()
                confirm_pw = confirm_pass_entry.get()
                doctor_pw = doctor_pass_entry.get()

                if new_pw != confirm_pw:
                    raise ValueError("Passwords do not match")
                if doctor_pw != self.current_user.password:
                    raise ValueError("Incorrect doctor password")

                mask = patients_df['id'] == pid
                if patients_df[mask].empty:
                    raise ValueError("Patient not found")

                patients_df.loc[mask, 'password'] = new_pw
                save_data()
                logging.info(f"Password changed for patient {pid} by doctor {self.current_user.id}")
                messagebox.showinfo("Success", "Password changed!")
                popup.destroy()
            except Exception as e:
                logging.error(f"Change password error: {str(e)}")
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Change Password", command=save,
                  bg="#10b981", fg="white", font=("Arial", 12, "bold")).pack(pady=25)

    def add_patient(self):
        popup = tk.Toplevel(self)
        popup.title("Add New Patient")
        popup.geometry("450x400")

        fields = [("Name:", "name"), ("Age:", "age"),
                  ("Ailment:", "ailment"), ("Password:", "password", True)]

        entries = {}
        for lbl, key, *extra in fields:
            tk.Label(popup, text=lbl).pack(pady=5)
            show = "*" if extra else ""
            entries[key] = tk.Entry(popup, show=show, width=40)
            entries[key].pack(pady=5)

        # Auto-generate Patient ID
        pid = get_next_id(patients_df)
        tk.Label(popup, text=f"Patient ID: {pid} (Auto-generated)", font=("Arial", 12)).pack(pady=10)

        def save():
            try:
                new_patient = {
                    'id': pid,
                    'name': entries["name"].get(),
                    'age': int(entries["age"].get()),
                    'ailment': entries["ailment"].get(),
                    'password': entries["password"].get(),
                    'reports': [],
                    'bills': [],
                    'prescriptions': []
                }
                global patients_df
                patients_df = pd.concat([patients_df, pd.DataFrame([new_patient])], ignore_index=True)
                save_data()
                logging.info(f"New patient {pid} added")
                messagebox.showinfo("Success", "Patient added")
                popup.destroy()
                self.show_doctor_dashboard()
            except Exception as e:
                logging.error(f"Add patient error: {str(e)}")
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Save", command=save, bg="#10b981", fg="white").pack(pady=20)

    def schedule_appointment(self):
        popup = tk.Toplevel(self)
        popup.title("Schedule Appointment")
        popup.geometry("500x450")

        tk.Label(popup, text="New Appointment", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Patient selection
        tk.Label(popup, text="Select Patient:").pack(pady=5)
        patient_list = [(row['id'], f"{row['id']} - {row['name']}") for _, row in patients_df.iterrows()]
        if not patient_list:
            messagebox.showwarning("No Patients", "Please add patients first")
            popup.destroy()
            return

        patient_var = tk.StringVar()
        patient_combo = ttk.Combobox(popup, textvariable=patient_var,
                                     values=[name for _, name in patient_list], width=40, state="readonly")
        patient_combo.pack(pady=5)
        patient_combo.current(0)

        fields = [("Date (YYYY-MM-DD):", "date"), ("Time (HH:MM):", "time")]

        entries = {}
        for lbl, key in fields:
            tk.Label(popup, text=lbl).pack(pady=5)
            entries[key] = tk.Entry(popup, width=40)
            entries[key].pack(pady=5)

        # Auto-generate Appointment ID
        app_id = get_next_id(appointments_df)
        tk.Label(popup, text=f"Appointment ID: {app_id} (Auto-generated)", font=("Arial", 12)).pack(pady=10)

        def save():
            try:
                # Get selected patient ID
                selected_name = patient_var.get()
                patient_id = next(pid for pid, name in patient_list if name == selected_name)

                new_app = {
                    'id': app_id,
                    'patient_id': patient_id,
                    'doctor_id': self.current_user.id,
                    'date': entries["date"].get() or datetime.now().strftime("%Y-%m-%d"),
                    'time': entries["time"].get()
                }
                global appointments_df
                appointments_df = pd.concat([appointments_df, pd.DataFrame([new_app])], ignore_index=True)
                save_data()
                logging.info(f"New appointment {app_id} scheduled")
                messagebox.showinfo("Success", "Appointment scheduled!")
                popup.destroy()
                self.show_doctor_dashboard()
            except Exception as e:
                logging.error(f"Schedule appointment error: {str(e)}")
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Schedule", command=save,
                  bg="#3b82f6", fg="white", font=("Arial", 12, "bold")).pack(pady=25)

    def export_patients_csv(self):
        try:
            export_df = patients_df[['id', 'name', 'age', 'ailment']].copy()
            export_df.to_csv('patients_export.csv', index=False)
            messagebox.showinfo("Success", "Patients exported to patients_export.csv")
            logging.info("Patients exported to CSV")
        except Exception as e:
            logging.error(f"Export patients error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def export_bills_csv(self):
        if not hasattr(self, 'current_bill_patient') or not self.current_bill_patient:
            messagebox.showwarning("No Patient", "Please select patient first")
            return
        try:
            bills = self.current_bill_patient.bills
            bills_df = pd.DataFrame([b.to_dict() for b in bills]) if bills else pd.DataFrame()
            bills_df.to_csv(f"bills_{self.current_bill_patient.id}.csv", index=False)
            messagebox.showinfo("Success", f"Bills exported to bills_{self.current_bill_patient.id}.csv")
            logging.info(f"Bills exported for patient {self.current_bill_patient.id}")
        except Exception as e:
            logging.error(f"Export bills error: {str(e)}")
            messagebox.showerror("Error", str(e))

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    load_data()

    if doctors_df.empty:
        print("\n" + "="*70)
        print("NO DOCTORS FOUND → Creating default admin doctor...")
        default = {'id': 1001, 'name': "Dr. Admin", 'specialization': "Administrator", 'password': "admin123"}
        doctors_df = pd.concat([doctors_df, pd.DataFrame([default])], ignore_index=True)
        save_data()
        print("Default Doctor: ID = 1001 | Password = admin123")
        print("="*70 + "\n")

    app = HospitalManagementSystem()

    app.mainloop()
