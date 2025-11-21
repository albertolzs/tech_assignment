# NBIM Regulatory News Dashboard

This is a minimal technical assignment delivering a dashboard that fetches regulatory news for Norges 
Bank Investment Management's five biggest markets.

<p align="center">
  <img alt="framework" src="https://raw.githubusercontent.com/albertolzs/tech_assignment/refs/heads/main/figures/framework.png">
</p>

## Quick start

First, clone the repository:
```bash
    git clone https://github.com/albertolzs/tech_assignment.git
```

Then, we offer you two options.

### Using docker

This is the easiest way to see the dashboard.

Build the image:
```bash
  docker build -t nbim-news:latest .
```

Note: You will need to set the OLLAMA_HOST to connect to your local Ollama instance.

Run:
```bash
    docker run --name nbim-news \
      -v "$(pwd)/news_info.db":/app/news_info.db \
      --add-host=host.docker.internal:host-gateway \
      -e OLLAMA_HOST=http://host.docker.internal:11434 \
      nbim-news:latest
```

Then open the link in your browser.

### Creating yourself the framework

1. Create and activate a virtual environment (optional but recommended)
```bash
   uv venv --python 3.13
   source .venv/bin/activate
```

2. Install dependencies
```bash
   uv pip install -r requirements.txt
```

3. Install and start Ollama with a model

```bash
  curl -fsSL https://ollama.com/install.sh | sh
```
Pull a small, capable model (e.g. Llama 3.1 8B):
```bash
  ollama pull llama3.2:1b
```

4. Run the dashboard

   streamlit run app.py

5. Open the provided local URL in your browser (typically http://localhost:8501).
