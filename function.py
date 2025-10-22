# your_function.py
import pandas as pd
import numpy as np

def divide_workload(df, N):
    # ตรวจสอบว่า df มีคอลัมน์ 'task' และ 'workload'
    if not all(col in df.columns for col in ['task', 'workload']):
        raise ValueError("DataFrame must contain 'task' and 'workload' columns.")

    # เรียงงานตาม workload จากมากไปน้อย เพื่อช่วยในการแบ่งแบบ greedy
    # ใช้ .copy() เพื่อหลีกเลี่ยง SettingWithCopyWarning ถ้าคุณจะแก้ไข df_sorted ต่อไป
    df_sorted = df.sort_values(by='workload', ascending=False).reset_index(drop=True)

    # สร้าง list ของ DataFrames สำหรับแต่ละคน
    # แต่ละ DataFrame จะเก็บงานของพนักงานแต่ละคน
    employee_tasks = [pd.DataFrame(columns=df.columns) for _ in range(N)]
    employee_workloads = np.zeros(N)

    # วนลูปเพื่อแบ่งงาน (ตัวอย่าง: Greedy approach)
    for index, row in df_sorted.iterrows():
        # หาน้อยที่สุดใน employee_workloads
        min_workload_idx = np.argmin(employee_workloads)

        # เพิ่มงานเข้าไปในคนที่มี workload น้อยที่สุด
        employee_tasks[min_workload_idx] = pd.concat([employee_tasks[min_workload_idx], pd.DataFrame([row])], ignore_index=True)
        employee_workloads[min_workload_idx] += row['workload']
        
    return employee_tasks