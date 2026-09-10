import socketio
import eventlet

# Initialize Socket.IO server with CORS enabled for your React app
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print(f"✅ Player connected: {sid}")
    # Send a confirmation message to the connected client
    sio.emit('server_message', {'data': 'Connected to Onyx Real-Time Server!'}, room=sid)

@sio.event
def disconnect(sid):
    print(f"❌ Player disconnected: {sid}")

if __name__ == '__main__':
    print("🚀 Starting Onyx Socket.IO Server on http://127.0.0.1:5000 ...")
    eventlet.wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)