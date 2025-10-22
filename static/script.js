document.addEventListener('DOMContentLoaded', () => {
    const excelFile = document.getElementById('excelFile');
    const numPeople = document.getElementById('numPeople');
    const uploadButton = document.getElementById('uploadButton');
    const loadingSpinner = document.getElementById('loading');
    const messageDiv = document.getElementById('message');
    const resultsDiv = document.getElementById('results');
    const resultTableBody = document.querySelector('#resultTable tbody');
    const finalVarianceSpan = document.getElementById('finalVariance');
    const downloadLink = document.getElementById('downloadLink');

    uploadButton.addEventListener('click', async () => {
        const file = excelFile.files[0];
        const N = parseInt(numPeople.value);

        // รีเซ็ตการแสดงผล
        messageDiv.textContent = '';
        messageDiv.className = 'message';
        resultsDiv.style.display = 'none';
        downloadLink.style.display = 'none';
        resultTableBody.innerHTML = ''; // เคลียร์ตารางเก่า

        if (!file) {
            showMessage('โปรดเลือกไฟล์ Excel', 'error');
            return;
        }

        if (isNaN(N) || N <= 0) {
            showMessage('จำนวนคนต้องเป็นตัวเลขจำนวนเต็มบวก', 'error');
            return;
        }

        if (!file.name.endsWith('.xlsx')) {
            showMessage('ไฟล์ที่อัปโหลดต้องเป็นนามสกุล .xlsx เท่านั้น', 'error');
            return;
        }

        uploadButton.disabled = true;
        loadingSpinner.style.display = 'block';
        showMessage('กำลังประมวลผล...', 'info');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('num_people', N);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showMessage('ประมวลผลสำเร็จ!', 'success');
                resultsDiv.style.display = 'block';
                finalVarianceSpan.textContent = data.final_variance.toFixed(2); // แสดงทศนิยม 2 ตำแหน่ง

                data.result_data.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.task}</td>
                        <td>${row.workload}</td>
                        <td>${row.label}</td>
                    `;
                    resultTableBody.appendChild(tr);
                });

                downloadLink.href = data.download_url;
                downloadLink.style.display = 'inline-block';

            } else {
                showMessage(`เกิดข้อผิดพลาด: ${data.error}`, 'error');
            }
        } catch (error) {
            showMessage(`เกิดข้อผิดพลาดในการเชื่อมต่อ: ${error.message}`, 'error');
            console.error('Fetch error:', error);
        } finally {
            uploadButton.disabled = false;
            loadingSpinner.style.display = 'none';
        }
    });

    function showMessage(msg, type) {
        messageDiv.textContent = msg;
        messageDiv.className = `message ${type}`;
    }
});