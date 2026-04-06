# Running ONYX in Different Environments

## Environment Types

### 1. Local Linux Desktop (Recommended)

**Best for**: Daily use, full functionality

```bash
cd /app
python3 desktop_app/main.py
```

**Requirements**:
- X11 or Wayland display server
- Audio input device
- Qt libraries installed

**Features Available**:
- ✓ Full GUI
- ✓ Voice input
- ✓ All AI features
- ✓ Local storage

---

### 2. Remote Server with X11 Forwarding

**Best for**: Testing on remote machines

```bash
# Connect with X11 forwarding
ssh -X user@remote-server

cd /app
export DISPLAY=:0
python3 desktop_app/main.py
```

**Requirements**:
- SSH with X11 forwarding enabled
- X11 libraries on server
- Local X server on client

**Features Available**:
- ✓ Full GUI (may be slow)
- ✗ Voice input (local mic not forwarded)
- ✓ All AI features
- ✓ Local storage

---

### 3. Docker Container (Experimental)

For containerized deployment:

```dockerfile
# Dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    qtbase5-dev \
    portaudio19-dev \
    libxcb-xinerama0 \
    libxcb-cursor0

COPY . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

CMD ["python3", "desktop_app/main.py"]
```

Run with X11 socket:
```bash
docker run -it \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/Onyx:/app/Onyx \
    onyx-app
```

**Features Available**:
- ✓ Full GUI
- ✗ Voice input (complicated in Docker)
- ✓ All AI features
- ✓ Persistent storage (via volume)

---

### 4. Headless Server (Not Supported)

**ONYX requires a display server**. It cannot run in headless mode.

If you need headless operation, consider:
- Using Xvfb (virtual framebuffer)
- Creating a separate CLI version
- Using VNC for remote GUI

**Xvfb Example**:
```bash
# Install Xvfb
sudo apt-get install xvfb

# Run with virtual display
xvfb-run python3 desktop_app/main.py
```

---

### 5. Kubernetes/Cloud Container

**Current Environment**: This is where ONYX is being developed.

**Limitations**:
- No display server available
- Cannot run GUI directly
- Voice input not available

**Workarounds**:
1. **Development/Testing**: Run tests without GUI
   ```bash
   python3 test_onyx.py
   ```

2. **Export for Local Use**: Package application for deployment
   ```bash
   tar -czf onyx-app.tar.gz desktop_app/ Onyx/ requirements.txt README.md
   ```

3. **Convert to Web App**: Create FastAPI + React version (separate project)

---

## Feature Matrix

| Feature | Local Desktop | SSH X11 | Docker | Headless | K8s |
|---------|--------------|---------|--------|----------|-----|
| GUI | ✓ | ✓ | ✓ | ✗ | ✗ |
| Voice Input | ✓ | ✗ | ✗ | ✗ | ✗ |
| AI Chat | ✓ | ✓ | ✓ | N/A | N/A |
| Storage | ✓ | ✓ | ✓ | N/A | N/A |
| Performance | Excellent | Good | Good | N/A | N/A |

---

## Deployment Scenarios

### Home Use
**Recommended**: Local Linux Desktop
```bash
cd /app
python3 desktop_app/main.py
```

### Office Network
**Recommended**: Local install on each machine
```bash
# Clone/copy to each machine
git clone <repo> ~/onyx
cd ~/onyx
pip install -r requirements.txt
python3 desktop_app/main.py
```

### Remote Access
**Recommended**: SSH with X11 forwarding
```bash
ssh -X user@server
cd /app
python3 desktop_app/main.py
```

### Multi-User Server
**Recommended**: Individual installs in home directories
```bash
# Each user:
cd ~
cp -r /app/desktop_app .
cp /app/requirements.txt .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 desktop_app/main.py
```

---

## Current Environment Note

**You are in a Kubernetes container environment.**

This environment:
- ✓ Perfect for developing the code
- ✓ Testing business logic
- ✓ Building and packaging
- ✗ Cannot run the GUI directly
- ✗ No display server available

**To use ONYX**:
1. Package the application:
   ```bash
   tar -czf onyx-linux-desktop.tar.gz \
       desktop_app/ \
       Onyx/ \
       requirements.txt \
       README.md \
       INSTALL.md \
       run_onyx.sh
   ```

2. Transfer to a Linux desktop:
   ```bash
   scp onyx-linux-desktop.tar.gz user@desktop:~/
   ```

3. Extract and run:
   ```bash
   tar -xzf onyx-linux-desktop.tar.gz
   cd onyx-linux-desktop
   pip install -r requirements.txt
   python3 desktop_app/main.py
   ```

---

## Testing Without GUI

In the current environment, you can test:

```bash
# Test imports and setup
python3 test_onyx.py

# Test storage service
python3 -c "
from desktop_app.services.storage_service import StorageService
storage = StorageService()
storage.initialize()
print('Storage OK')
"

# Test chat service (requires API key)
python3 -c "
import asyncio
from desktop_app.services.chat_service import ChatService
from desktop_app.services.storage_service import StorageService

storage = StorageService()
storage.initialize()
chat_id = storage.create_chat('Test')

async def test():
    chat = ChatService()
    response = await chat.send_message('Say hi', chat_id)
    print(f'Response: {response[:100]}...')

asyncio.run(test())
"
```

---

## Production Deployment

For production use:

1. **Single User**: Install directly on Linux desktop
2. **Multiple Users**: Network-shared installation with individual data folders
3. **Enterprise**: Consider converting to web-based architecture

**This application is designed for Linux desktop use, not for web deployment.**

---

## Support

For environment-specific issues:
- Check `Onyx/logs/onyx_*.log`
- Verify Qt libraries: `ldd $(which python3)`
- Test display: `echo $DISPLAY`
- Check X11: `xdpyinfo`

For GUI issues:
```bash
export QT_DEBUG_PLUGINS=1
python3 desktop_app/main.py
```
