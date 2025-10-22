import os
from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import numpy as np
import random
from scipy.stats import variation

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# สร้างโฟลเดอร์ถ้ายังไม่มี
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# --- Genetic Algorithm Implementation ---

def calculate_variance(chromosome, tasks, N):
    """
    คำนวณความแปรปรวนของ workload ของแต่ละกลุ่ม
    """
    group_workloads = [0.0] * N
    for i, label in enumerate(chromosome):
        group_workloads[label - 1] += tasks[i]['workload']
    
    if len(group_workloads) > 1:
        return np.var(group_workloads)
    else:
        return 0.0 # ถ้ามีแค่กลุ่มเดียว ความแปรปรวนเป็น 0

def create_initial_population(num_tasks, N, pool_size=1000):
    """
    สร้างประชากรเริ่มต้น (chromosome)
    """
    population = []
    for _ in range(pool_size):
        chromosome = [random.randint(1, N) for _ in range(num_tasks)]
        population.append(chromosome)
    return population

def selection(population, tasks, N, num_selected=50):
    """
    คัดเลือก chromosome ที่มี fitness (variance) ต่ำที่สุด
    """
    # คำนวณ fitness (variance) สำหรับแต่ละ chromosome
    fitness_scores = [(chromosome, calculate_variance(chromosome, tasks, N)) for chromosome in population]
    
    # เรียงลำดับจากน้อยไปมาก (variance ต่ำที่สุดคือดีที่สุด)
    fitness_scores.sort(key=lambda x: x[1])
    
    # เลือก num_selected อันดับแรก
    return [item[0] for item in fitness_scores[:num_selected]]

def crossover(parent1, parent2):
    """
    การผสมข้าม (Crossover) แบบ single-point crossover
    """
    if len(parent1) < 2:
        return parent1, parent2 # ไม่สามารถทำ crossover ได้ถ้าความยาวน้อยกว่า 2
    
    crossover_point = random.randint(1, len(parent1) - 1)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    return child1, child2

def mutate_change(chromosome, N, mutation_rate=0.1):
    """
    การกลายพันธุ์แบบ Change Mutation: เปลี่ยนค่า label ในตำแหน่งสุ่ม
    """
    mutated_chromosome = list(chromosome) # สร้างสำเนาเพื่อไม่ให้กระทบ chromosome เดิม
    for i in range(len(mutated_chromosome)):
        if random.random() < mutation_rate:
            mutated_chromosome[i] = random.randint(1, N)
    return mutated_chromosome

def mutate_swap(chromosome, N, mutation_rate=0.1):
    """
    การกลายพันธุ์แบบ Swap Mutation: สลับค่า label สองตำแหน่ง
    """
    mutated_chromosome = list(chromosome)
    if random.random() < mutation_rate and len(mutated_chromosome) >= 2:
        idx1, idx2 = random.sample(range(len(mutated_chromosome)), 2)
        mutated_chromosome[idx1], mutated_chromosome[idx2] = mutated_chromosome[idx2], mutated_chromosome[idx1]
    return mutated_chromosome

def generate_new_population(selected_chromosomes, num_tasks, N, pool_size=1000, mutation_rate=0.1):
    """
    สร้างประชากรใหม่โดยใช้ crossover และ mutation
    """
    new_population = list(selected_chromosomes) # เก็บ chromosome ที่ดีที่สุดไว้
    
    # เติมเต็ม population ด้วย crossover และ mutation
    while len(new_population) < pool_size:
        parent1 = random.choice(selected_chromosomes)
        parent2 = random.choice(selected_chromosomes)
        
        child1, child2 = crossover(parent1, parent2)
        
        # ใช้ทั้งสองแบบของการกลายพันธุ์
        child1 = mutate_change(child1, N, mutation_rate)
        child1 = mutate_swap(child1, N, mutation_rate)
        
        child2 = mutate_change(child2, N, mutation_rate)
        child2 = mutate_swap(child2, N, mutation_rate)
        
        new_population.append(child1)
        if len(new_population) < pool_size:
            new_population.append(child2)
            
    return new_population

def genetic_algorithm(tasks_data, N, generations=500, pool_size=1000, num_selected=50, mutation_rate=0.1):
    """
    ฟังก์ชันหลักของ Genetic Algorithm
    """
    num_tasks = len(tasks_data)
    if num_tasks == 0:
        return []

    population = create_initial_population(num_tasks, N, pool_size)
    
    best_chromosome = None
    min_variance = float('inf')

    for gen in range(generations):
        selected_chromosomes = selection(population, tasks_data, N, num_selected)
        
        # ตรวจสอบ chromosome ที่ดีที่สุดในรุ่นปัจจุบัน
        current_best_chromosome = selected_chromosomes[0]
        current_variance = calculate_variance(current_best_chromosome, tasks_data, N)

        if current_variance < min_variance:
            min_variance = current_variance
            best_chromosome = current_best_chromosome
            
        population = generate_new_population(selected_chromosomes, num_tasks, N, pool_size, mutation_rate)
        
        # print(f"Generation {gen+1}: Best Variance = {min_variance:.2f}") # สำหรับ debug

    # ตรวจสอบ chromosome ที่ดีที่สุดอีกครั้งหลังจากจบ loop
    if best_chromosome is None:
        # หากไม่พบ best_chromosome ใน loop (เช่น num_selected น้อยกว่า 1)
        # ให้หาจาก population สุดท้าย
        fitness_scores = [(chromosome, calculate_variance(chromosome, tasks_data, N)) for chromosome in population]
        fitness_scores.sort(key=lambda x: x[1])
        best_chromosome = fitness_scores[0][0]
        min_variance = fitness_scores[0][1]

    return best_chromosome, min_variance

# --- Flask Routes ---

@app.route('/')
def index():
    """
    หน้าหลักของ Web App
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    API สำหรับอัปโหลดไฟล์ Excel และรัน Genetic Algorithm
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.endswith('.xlsx'):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            df = pd.read_excel(filepath)
            
            if 'task' not in df.columns or 'workload' not in df.columns:
                return jsonify({'error': 'Excel file must contain "task" and "workload" columns.'}), 400

            num_people = int(request.form.get('num_people', 1))
            if num_people <= 0:
                return jsonify({'error': 'Number of people must be a positive integer.'}), 400
            
            tasks_data = df[['task', 'workload']].to_dict('records')
            
            # รัน Genetic Algorithm
            best_labels, final_variance = genetic_algorithm(tasks_data, num_people)
            
            # เพิ่มคอลัมน์ 'label' ลงใน DataFrame
            df['label'] = best_labels
            
            # เตรียมข้อมูลสำหรับแสดงผลบนหน้าเว็บ
            result_data = df.to_dict('records')
            
            # บันทึกผลลัพธ์เป็นไฟล์ Excel เพื่อดาวน์โหลด
            output_filename = f"งานแบ่งแล้ว_{file.filename}"
            output_filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], output_filename)
            df.to_excel(output_filepath, index=False)
            
            return jsonify({
                'success': True,
                'result_data': result_data,
                'final_variance': final_variance,
                'download_url': f'/download/{output_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type. Please upload an Excel (.xlsx) file.'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    """
    API สำหรับดาวน์โหลดไฟล์ผลลัพธ์
    """
    filepath = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found.'}), 404

if __name__ == '__main__':
    app.run(debug=True) # debug=True สำหรับการพัฒนา