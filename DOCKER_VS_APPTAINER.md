# Docker vs Apptainer Usage

## Key Differences

### User ID (File Ownership)

**Docker:**
- Runs as **root (UID 0)** inside container by default
- Files created in mounted volumes are owned by root on the host
- **Solution**: Use `--user $(id -u):$(id -g)` flag

**Apptainer/Singularity:**
- Automatically runs as **your own UID**
- Files are created with your ownership
- No special flags needed

### Running the Images

#### With Docker (requires --user flag):

```bash
# Run interactively
docker run --rm -it --user $(id -u):$(id -g) -v $PWD:/workspace snakepit:u20

# Create a venv and install packages
docker run --rm --user $(id -u):$(id -g) -v $PWD:/workspace snakepit:u24 bash -c "
    python3.12 -m venv venv
    python3.12 -m pip install numpy scipy
"
```

#### With Apptainer (no special flags):

```bash
# Run interactively
apptainer shell snakepit_u20.sif

# Create a venv and install packages
apptainer exec snakepit_u24.sif bash -c "
    python3.12 -m venv venv
    python3.12 -m pip install numpy scipy
"
```

### Converting Docker Images to Apptainer

```bash
# Pull Docker image and convert to SIF
apptainer build snakepit_u20.sif docker-daemon://snakepit:u20
apptainer build snakepit_u24.sif docker-daemon://snakepit:u24
```

## Important: Always Use Versioned Python Commands

Never use bare `python` or `pip` commands. Always specify the version:

```bash
# ✓ CORRECT
python2.7 -m pip install numpy
python3.12 -m venv my_venv

# ✗ WRONG
pip install numpy
python -m venv my_venv
```

This ensures you're using the exact Python version you intend to test.
