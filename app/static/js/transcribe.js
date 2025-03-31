document.getElementById('transcription-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const progress = document.getElementById('progress');
    const status = document.getElementById('status');
    
    try {
        progress.style.display = 'block';
        form.style.display = 'none';
        
        const response = await fetch('/transcribe', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Transcription failed');
        }
        
        status.textContent = 'Transcription completed successfully!';
        
        // Download the transcript
        window.location.href = `/download/${encodeURIComponent(data.transcript_path)}`;
        
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
        progress.classList.add('error');
    }
}); 