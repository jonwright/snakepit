# Snakepit: Multi-Python Docker Images for Testing Scientific Extensions

Docker/Apptainer images for testing scientific Python C extensions across multiple Python versions, from legacy Python 2.7 to modern Python 3.12.

## Quick Start

### Build the Images

```bash
docker build -f Dockerfile.u20 -t snakepit:u20 .
docker build -f Dockerfile.u24 -t snakepit:u24 .
```

### Run a Container

```bash
# For Python 2.7 or 3.8
docker run -it -v $(pwd):/workspace snakepit:u20

# For Python 3.12
docker run -it -v $(pwd):/workspace snakepit:u24
```

## Images

### snakepit:u20 (Ubuntu 20.04)
- Python 2.7
- Python 3.8
- Ideal for testing legacy code

### snakepit:u24 (Ubuntu 24.04)
- Python 3.12
- Modern Python testing

## Typical Workflow

1. **Mount your project directory** into the container:
   ```bash
   docker run -it -v /path/to/project:/workspace snakepit:u20
   ```

2. **Create a virtual environment** for the desired Python version:
   ```bash
   # Inside the container
   python2.7 -m venv venv_py27
   source venv_py27/bin/activate
   ```

3. **Install numpy and scipy**:
   ```bash
   pip install numpy scipy
   ```

4. **Build your C extension** using f2py or direct compilation

5. **Test your extension** across different Python versions by repeating steps 2-4 with different Python binaries

## Testing

Run the test script to verify the images work correctly:

```bash
./test_images.sh
```

This script requires a test C extension in `../test_extension/` (see specification.md for details).

## Documentation

See [specification.md](specification.md) for complete details on:
- Image contents
- Build approach
- Design rationale
- Example C extension structure

## License

Public domain / MIT (choose your preference)
