#!/bin/bash

# Define container and image names
IMAGE_NAME="duplicate-finder"
CONTAINER_NAME="duplicate-finder-container"
BUILD_DIR="./docker_build"

echo "🚀 Starting Duplicate Finder..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if the image exists, build it if missing
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
    echo "🔨 Preparing build environment..."

    # Create a temporary directory for the Docker build
    rm -rf "$BUILD_DIR" && mkdir "$BUILD_DIR"

    # Copy necessary files into the build directory
    cp find_duplicates.py "$BUILD_DIR/"
    cp requirements.txt "$BUILD_DIR/"

    # Create Dockerfile inside the build directory
    cat > "$BUILD_DIR/Dockerfile" <<EOF
# Use a lightweight Python image
FROM python:3.11-slim
WORKDIR /app
COPY find_duplicates.py .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "find_duplicates.py"]
EOF

    echo "🔨 Building the Docker image..."
    docker build -t "$IMAGE_NAME" "$BUILD_DIR"

    # Cleanup temporary build directory
    rm -rf "$BUILD_DIR"

    if [ $? -eq 0 ]; then
        echo "✅ Docker image built successfully."
    else
        echo "❌ Docker image build failed."
        exit 1
    fi
fi

# Check if a container is already running
if [[ "$(docker ps -q -f name=$CONTAINER_NAME)" ]]; then
    echo "⚠️ Container is already running! Stopping it..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# Run the container
echo "🔍 Running Duplicate Finder..."
echo "📂 Your host machine is mounted inside the container at: /mnt"
docker run --rm -it --privileged --name "$CONTAINER_NAME" -v /:/mnt "$IMAGE_NAME"

echo "✅ Duplicate Finder finished."
echo "📂 Your host machine is mounted inside the container at: /mnt"