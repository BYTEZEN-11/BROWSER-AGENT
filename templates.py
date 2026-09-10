"""
Ultra Attractive UI Templates with Glassmorphism, 3D Effects, Particles
"""

ULTRA_ATTRACTIVE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }} - {{ app_description }}</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --secondary: #6366f1;
            --accent: #06b6d4;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark-bg: #090d16;
            --card-bg: rgba(15, 23, 42, 0.85);
            --card-border: rgba(148, 163, 184, 0.15);
            --glass-bg: rgba(15, 23, 42, 0.8);
            --glass-border: rgba(148, 163, 184, 0.15);
        }
        
        body {
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #090d16;
            background-image: 
                radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 0%, rgba(79, 70, 229, 0.15) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(6, 182, 212, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
            color: #f1f5f9;
        }
        
        /* Particle Background */
        #particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            pointer-events: none;
        }
        
        .particle {
            position: absolute;
            background: rgba(59, 130, 246, 0.25);
            border-radius: 50%;
            animation: float 20s infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
            10% { opacity: 0.6; }
            90% { opacity: 0.6; }
            100% { transform: translateY(-100vh) translateX(60px); opacity: 0; }
        }
        
        /* Glass Container */
        .container {
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        
        /* Glassmorphism Card */
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            box-shadow: 
                0 10px 40px -10px rgba(0, 0, 0, 0.6),
                0 0 0 1px rgba(255, 255, 255, 0.05);
            padding: 35px;
            margin-bottom: 25px;
            animation: fadeInUp 0.5s ease-out;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .glass-card:hover {
            transform: translateY(-4px);
            border-color: rgba(59, 130, 246, 0.35);
            box-shadow: 
                0 20px 50px -10px rgba(0, 0, 0, 0.7),
                0 0 30px rgba(59, 130, 246, 0.12);
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Header Styles */
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .logo-container {
            perspective: 1000px;
            margin-bottom: 20px;
        }
        
        .logo {
            font-size: 120px;
            display: inline-block;
            animation: rotate3D 10s infinite;
            filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.5));
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .logo:hover {
            animation-play-state: paused;
            transform: scale(1.2);
        }
        
        @keyframes rotate3D {
            0% { transform: rotateY(0deg) rotateX(0deg); }
            50% { transform: rotateY(180deg) rotateX(20deg); }
            100% { transform: rotateY(360deg) rotateX(0deg); }
        }
        
        h1 {
            font-size: 3.5em;
            font-weight: 900;
            background: linear-gradient(45deg, #fff, #f093fb, #fff);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 3s linear infinite;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
            margin-bottom: 15px;
            letter-spacing: 2px;
        }
        
        @keyframes shimmer {
            0% { background-position: 0% center; }
            100% { background-position: 200% center; }
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.4em;
            font-weight: 300;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        .version-badge {
            display: inline-block;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
            backdrop-filter: blur(10px);
            color: white;
            padding: 10px 25px;
            border-radius: 50px;
            font-size: 0.9em;
            font-weight: 600;
            margin-top: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        /* Card Header */
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.2);
        }
        
        .card-icon {
            font-size: 40px;
            margin-right: 15px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .card-header h2 {
            color: white;
            font-size: 1.8em;
            font-weight: 700;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
        
        /* Form Styles */
        .form-group {
            margin-bottom: 25px;
        }
        
        label {
            display: block;
            color: white;
            font-weight: 600;
            font-size: 1.05em;
            margin-bottom: 10px;
            text-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        }
        
        label i {
            margin-right: 10px;
            color: var(--accent);
        }
        
        input, textarea, select {
            width: 100%;
            padding: 16px 20px;
            background: rgba(10, 15, 29, 0.75);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            font-size: 1rem;
            font-family: inherit;
            color: #f8fafc;
            transition: all 0.25s ease;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        input::placeholder, textarea::placeholder {
            color: rgba(148, 163, 184, 0.5);
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            background: rgba(15, 23, 42, 0.95);
            border-color: #3b82f6;
            box-shadow: 
                0 0 0 3px rgba(59, 130, 246, 0.25),
                0 8px 24px rgba(0, 0, 0, 0.3);
            transform: none;
        }
        
        textarea {
            min-height: 140px;
            resize: vertical;
        }
        
        .input-hint {
            font-size: 0.85em;
            color: rgba(148, 163, 184, 0.7);
            margin-top: 8px;
            margin-left: 4px;
        }
        
        /* Modern Button */
        button {
            width: 100%;
            padding: 18px 32px;
            background: linear-gradient(135deg, #2563eb, #4f46e5);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4);
            letter-spacing: 0.5px;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        button:hover {
            background: linear-gradient(135deg, #1d4ed8, #4338ca);
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.6);
        }
        
        button:hover::before {
            left: 100%;
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            background: rgba(148, 163, 184, 0.2);
            color: rgba(148, 163, 184, 0.5);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        button i {
            margin-right: 10px;
        }
        
        /* Status Alerts */
        .status {
            padding: 16px 24px;
            border-radius: 12px;
            margin-bottom: 25px;
            font-weight: 500;
            display: none;
            animation: slideInRight 0.4s ease-out;
            backdrop-filter: blur(10px);
            border: 1px solid;
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .status.show {
            display: flex;
            align-items: center;
        }
        
        .status i {
            font-size: 1.3em;
            margin-right: 12px;
        }
        
        .status.success {
            background: rgba(16, 185, 129, 0.12);
            border-color: rgba(16, 185, 129, 0.35);
            color: #34d399;
        }
        
        .status.error {
            background: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.35);
            color: #f87171;
        }
        
        .status.loading {
            background: rgba(59, 130, 246, 0.12);
            border-color: rgba(59, 130, 246, 0.35);
            color: #60a5fa;
        }
        
        /* Results */
        .result-box {
            background: rgba(10, 15, 29, 0.75);
            backdrop-filter: blur(10px);
            padding: 24px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            margin-top: 20px;
            color: #f8fafc;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .result-label {
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            color: #f8fafc;
        }
        
        .result-label i {
            margin-right: 10px;
            color: var(--accent);
        }
        
        .url-box {
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.95em;
            background: rgba(2, 6, 23, 0.6);
            padding: 16px 20px;
            border-radius: 10px;
            overflow-wrap: break-word;
            border: 1px solid rgba(148, 163, 184, 0.15);
            color: #38bdf8;
        }
        
        .steps {
            max-height: 450px;
            overflow-y: auto;
            background: rgba(2, 6, 23, 0.5);
            padding: 16px;
            border-radius: 12px;
            margin-top: 15px;
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        .steps::-webkit-scrollbar {
            width: 8px;
        }
        
        .steps::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 8px;
        }
        
        .steps::-webkit-scrollbar-thumb {
            background: rgba(148, 163, 184, 0.25);
            border-radius: 8px;
        }
        
        .step {
            padding: 14px 18px;
            margin-bottom: 12px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 10px;
            border-left: 3px solid #3b82f6;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
            transition: all 0.2s ease;
            backdrop-filter: blur(8px);
            animation: fadeInLeft 0.5s ease-out;
        }
        
        @keyframes fadeInLeft {
            from {
                opacity: 0;
                transform: translateX(-30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .step:hover {
            transform: translateX(10px);
            background: rgba(255, 255, 255, 0.2);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }
        
        /* Features Grid */
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .feature {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            text-align: center;
            border: 2px solid rgba(255, 255, 255, 0.2);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
        }
        
        .feature:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-10px) scale(1.05);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }
        
        .feature-icon {
            font-size: 3em;
            margin-bottom: 15px;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }
        
        .feature-text {
            font-weight: 600;
            font-size: 1.1em;
            color: white;
            text-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        }
        
        /* Loader */
        .loader-container {
            display: flex;
            justify-content: center;
            margin: 30px 0;
        }
        
        .loader {
            width: 60px;
            height: 60px;
            border: 5px solid rgba(255, 255, 255, 0.3);
            border-top: 5px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 50px;
            color: white;
        }
        
        .footer-links {
            margin: 20px 0;
        }
        
        .footer-link {
            display: inline-block;
            margin: 0 15px;
            color: white;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            padding: 10px 20px;
            border-radius: 50px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .footer-link:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            h1 { font-size: 2.5em; }
            .logo { font-size: 80px; }
            .glass-card { padding: 25px; }
            button { font-size: 1.1em; }
        }
        
        /* Floating Elements */
        .float-element {
            position: fixed;
            border-radius: 50%;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
            backdrop-filter: blur(5px);
            animation: floatRandom 20s infinite;
            z-index: 0;
        }
        
        @keyframes floatRandom {
            0%, 100% { transform: translate(0, 0) rotate(0deg); }
            25% { transform: translate(100px, 50px) rotate(90deg); }
            50% { transform: translate(50px, 100px) rotate(180deg); }
            75% { transform: translate(-50px, 50px) rotate(270deg); }
        }
    </style>
</head>
<body>
    <!-- Floating Background Elements -->
    <div class="float-element" style="width: 300px; height: 300px; top: 10%; left: 5%; animation-delay: 0s;"></div>
    <div class="float-element" style="width: 200px; height: 200px; top: 60%; right: 10%; animation-delay: 5s;"></div>
    <div class="float-element" style="width: 150px; height: 150px; bottom: 10%; left: 30%; animation-delay: 10s;"></div>
    
    <!-- Particles Container -->
    <div id="particles"></div>
    
    <div class="container">
        <!-- Header -->
        <div class="glass-card header">
            <div class="logo-container">
                <div class="logo">🤖</div>
            </div>
            <h1>{{ app_name }}</h1>
            <p class="subtitle">{{ app_description }}</p>
            <span class="version-badge">✨ v{{ app_version }}</span>
        </div>

        <!-- Configuration Card -->
        <div class="glass-card">
            <div class="card-header">
                <div class="card-icon">⚡</div>
                <h2>Agent Configuration</h2>
            </div>
            
            <div class="form-group">
                <label><i class="fas fa-key"></i> OpenAI API Key</label>
                <input type="password" id="apiKey" placeholder="sk-proj-your-api-key-here" required>
                <div class="input-hint">🔗 Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" style="color: var(--accent);">OpenAI Platform</a></div>
            </div>
            
            <div class="form-group">
                <label><i class="fas fa-tasks"></i> Task Description</label>
                <textarea id="task" placeholder="Example: Navigate to Hacker News and get the top 3 trending stories with their titles and points" required></textarea>
                <div class="input-hint">💡 Be specific about what you want the AI agent to accomplish</div>
            </div>
            
            <div class="form-group">
                <label><i class="fas fa-sliders-h"></i> Maximum Execution Steps</label>
                <input type="number" id="maxSteps" value="{{ default_max_steps }}" min="{{ min_max_steps }}" max="{{ max_max_steps }}">
                <div class="input-hint">🎯 Range: {{ min_max_steps }}-{{ max_max_steps }} steps (more steps = more complex tasks)</div>
            </div>
            
            <button onclick="runAgent()" id="runBtn">
                <i class="fas fa-rocket"></i> Execute AI Agent
            </button>
        </div>

        <!-- Status -->
        <div id="status" class="status"></div>

        <!-- Results -->
        <div id="results" style="display:none;">
            <div class="glass-card">
                <div class="card-header">
                    <div class="card-icon">📊</div>
                    <h2>Execution Results</h2>
                </div>
                <div id="resultContent"></div>
                <div id="urlBox" style="display:none;">
                    <div class="result-label"><i class="fas fa-link"></i> Final URL</div>
                    <div class="url-box" id="finalUrl"></div>
                </div>
                <div id="stepsBox" style="display:none;">
                    <div class="result-label"><i class="fas fa-list-ol"></i> Execution Steps</div>
                    <div class="steps" id="stepsList"></div>
                </div>
            </div>
        </div>

        <!-- Features -->
        <div class="glass-card">
            <div class="card-header">
                <div class="card-icon">🚀</div>
                <h2>Powered By</h2>
            </div>
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-text">{{ openai_model }}</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔗</div>
                    <div class="feature-text">LangGraph</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">🎭</div>
                    <div class="feature-text">Playwright</div>
                </div>
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-text">Python {{ python_version }}</div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p style="font-size: 1.2em; font-weight: 600;">Built with ❤️ for AI-Powered Automation</p>
            <div class="footer-links">
                <a href="/health" class="footer-link"><i class="fas fa-heartbeat"></i> Health Check</a>
                <a href="/config" class="footer-link"><i class="fas fa-cog"></i> Configuration</a>
            </div>
            <p style="margin-top: 15px; opacity: 0.8;">© 2026 {{ app_name }} • All Rights Reserved</p>
        </div>
    </div>

    <script>
        // Create particles
        function createParticles() {
            const container = document.getElementById('particles');
            for (let i = 0; i < 50; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.width = Math.random() * 5 + 2 + 'px';
                particle.style.height = particle.style.width;
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDuration = (Math.random() * 10 + 10) + 's';
                particle.style.animationDelay = Math.random() * 5 + 's';
                container.appendChild(particle);
            }
        }
        createParticles();

        // Agent execution
        async function runAgent() {
            const apiKey = document.getElementById('apiKey').value.trim();
            const task = document.getElementById('task').value.trim();
            const maxSteps = parseInt(document.getElementById('maxSteps').value);

            if (!apiKey) {
                showStatus('error', '<i class="fas fa-exclamation-triangle"></i> Please enter your OpenAI API key');
                return;
            }
            if (!task) {
                showStatus('error', '<i class="fas fa-exclamation-triangle"></i> Please enter a task description');
                return;
            }
            if (maxSteps < {{ min_max_steps }} || maxSteps > {{ max_max_steps }}) {
                showStatus('error', `<i class="fas fa-exclamation-triangle"></i> Max steps must be between {{ min_max_steps }} and {{ max_max_steps }}`);
                return;
            }

            const runBtn = document.getElementById('runBtn');
            runBtn.disabled = true;
            showStatus('loading', '<i class="fas fa-spinner fa-spin"></i> AI Agent is executing your task... This may take 1-3 minutes');
            document.getElementById('results').style.display = 'none';

            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        api_key: apiKey, 
                        task: task,
                        max_steps: maxSteps
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showStatus('success', '<i class="fas fa-check-circle"></i> Agent executed successfully!');
                    displayResults(data);
                    setTimeout(() => scrollToResults(), 300);
                } else {
                    showStatus('error', '<i class="fas fa-times-circle"></i> Error: ' + data.error);
                }
            } catch (error) {
                showStatus('error', '<i class="fas fa-exclamation-circle"></i> Network error: ' + error.message);
            } finally {
                runBtn.disabled = false;
            }
        }

        function showStatus(type, message) {
            const status = document.getElementById('status');
            status.className = 'status show ' + type;
            status.innerHTML = message;
            if (type === 'loading') {
                status.innerHTML += '<div class="loader-container"><div class="loader"></div></div>';
            }
        }

        function displayResults(data) {
            document.getElementById('results').style.display = 'block';
            document.getElementById('resultContent').innerHTML = 
                '<div class="result-box"><div class="result-label"><i class="fas fa-clipboard-check"></i> Result</div>' + 
                data.result + '</div>';
            
            if (data.url) {
                document.getElementById('urlBox').style.display = 'block';
                document.getElementById('finalUrl').textContent = data.url;
            }

            if (data.steps && data.steps.length > 0) {
                document.getElementById('stepsBox').style.display = 'block';
                document.getElementById('stepsList').innerHTML = 
                    data.steps.map((step, i) => '<div class="step" style="animation-delay: ' + (i * 0.1) + 's"><i class="fas fa-chevron-right"></i> ' + step + '</div>').join('');
            }
        }

        function scrollToResults() {
            document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // Keyboard shortcut
        document.getElementById('task').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                runAgent();
            }
        });

        // Logo click effect
        document.querySelector('.logo').addEventListener('click', function() {
            this.style.animation = 'none';
            setTimeout(() => { this.style.animation = ''; }, 10);
        });
    </script>
</body>
</html>
"""

