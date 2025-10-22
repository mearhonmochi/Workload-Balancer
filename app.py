# app.py
from flask import Flask, request, render_template, jsonify
import pandas as pd
import numpy as np
import io

app = Flask(__name__)

# ฟังก์ชันสำหรับแบ่งงาน (จากไฟล์ your_function.py)
# ผมขออนุมานว่าฟังก์ชันนี้ใช้ input เป็น DataFrame และ output เป็น DataFrame หรือ list of dicts
from your_function import divide_workload # สมมติว่านี่คือชื่อฟังก์ชันที่คุณใช้

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_and_calculate', methods=['POST'])
def upload_and_calculate():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Invalid file type. Only .xlsx files are allowed."}), 400

    try:
        # รับค่า N จากฟอร์ม
        N_str = request.form.get('num_people')
        try:
            N = int(N_str)
            if N <= 0:
                return jsonify({"error": "Number of people (N) must be a positive integer."}), 400
        except ValueError:
            return jsonify({"error": "Invalid value for N. Please enter a number."}), 400

        # --- จุดที่อาจเกิดปัญหา Memory ---
        # อ่านไฟล์ Excel โดยตรงจาก stream
        # เนื่องจาก Render มี RAM จำกัด การอ่านไฟล์ขนาดใหญ่อาจเป็นปัญหา
        file_content = io.BytesIO(file.read())
        
        # เพิ่มการจัดการ MemoryError
        try:
            df = pd.read_excel(file_content)
        except MemoryError:
            return jsonify({"error": "Memory limit exceeded while reading the Excel file. Try a smaller file or upgrade your hosting plan."}), 507
        except Exception as e: # จับข้อผิดพลาดอื่นๆ ที่อาจเกิดขึ้นขณะอ่านไฟล์
            return jsonify({"error": f"Error reading Excel file: {str(e)}"}), 400

        # ตรวจสอบว่าคอลัมน์ที่จำเป็นมีอยู่หรือไม่
        required_columns = ['task', 'workload']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            return jsonify({"error": f"Missing required columns in Excel file: {', '.join(missing_cols)}"}), 400
        
        # แปลง workload เป็น numeric และจัดการค่าที่ไม่ถูกต้อง
        # errors='coerce' จะเปลี่ยนค่าที่ไม่สามารถแปลงเป็นตัวเลขได้ให้เป็น NaN
        df['workload'] = pd.to_numeric(df['workload'], errors='coerce')
        # ลบแถวที่มี workload เป็น NaN ออก หรือจัดการตามความเหมาะสม
        df.dropna(subset=['workload'], inplace=True)
        
        if df.empty:
            return jsonify({"error": "No valid workload data found after cleaning."}), 400

        # --- เรียกใช้ฟังก์ชันแบ่งงานของคุณ ---
        # สมมติว่า divide_workload รับ df และ N แล้วส่งคืนผลลัพธ์ที่สามารถแปลงเป็น JSON ได้
        # คุณอาจต้องปรับผลลัพธ์จากฟังก์ชันของคุณให้เหมาะสม
        try:
            divided_tasks_raw = divide_workload(df, N)
            
            # แปลงผลลัพธ์ให้อยู่ในรูปแบบที่ client ต้องการ (เช่น list ของ dicts)
            # ตัวอย่าง: หาก divided_tasks_raw เป็น list ของ DataFrames
            # divided_tasks = []
            # for i, sub_df in enumerate(divided_tasks_raw):
            #     divided_tasks.append({f"Employee_{i+1}": sub_df.to_dict(orient='records')})

            # หรือหากเป็นรูปแบบอื่น คุณต้องปรับการแปลงตรงนี้
            # สำหรับตอนนี้ ผมจะสมมติว่ามันสามารถ jsonify ได้เลย
            
            # ตัวอย่างการส่งผลลัพธ์กลับในรูปแบบที่ซับซ้อนขึ้น
            # เช่น ถ้า divide_workload ส่งคืน list ของ DataFrames
            divided_tasks_jsonable = {}
            for i, employee_tasks_df in enumerate(divided_tasks_raw):
                # ตรวจสอบว่า employee_tasks_df ไม่ว่างเปล่าก่อนแปลง
                if not employee_tasks_df.empty:
                    divided_tasks_jsonable[f'Employee {i+1}'] = employee_tasks_df.to_dict(orient='records')
                else:
                    divided_tasks_jsonable[f'Employee {i+1}'] = []

            return jsonify({"success": True, "data": divided_tasks_jsonable})

        except MemoryError:
            return jsonify({"error": "Memory limit exceeded during workload division. Try a smaller file or upgrade your hosting plan."}), 507
        except Exception as e:
            return jsonify({"error": f"Error during workload division: {str(e)}"}), 500

    except Exception as e:
        # ข้อผิดพลาดที่ไม่คาดคิดอื่นๆ
        print(f"Unhandled error: {e}") # สำหรับ debug ใน server logs
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)