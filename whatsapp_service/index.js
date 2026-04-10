const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const cors = require('cors');
const qrcode = require('qrcode');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3001;

let qrDataUrl = '';
let isReady = false;

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './whatsapp_auth' }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-extensions']
    }
});

client.on('qr', async (qr) => {
    // Generate QR code data URL
    try {
        qrDataUrl = await qrcode.toDataURL(qr);
        console.log('QR Code generated. Please scan to connect.');
        isReady = false;
    } catch (err) {
        console.error('Failed to generate QR data URL', err);
    }
});

client.on('ready', () => {
    console.log('WhatsApp Client is ready!');
    isReady = true;
    qrDataUrl = ''; // Clear QR since we are connected
});

client.on('authenticated', () => {
    console.log('WhatsApp Authenticated. Generating session data...');
});

client.on('auth_failure', msg => {
    console.error('WhatsApp Authentication failure', msg);
    isReady = false;
});

client.on('disconnected', (reason) => {
    console.log('WhatsApp Client was logged out. Reason:', reason);
    isReady = false;
    qrDataUrl = '';
});

// Start WhatsApp client
client.initialize();

// API Endpoints
app.get('/status', (req, res) => {
    res.json({ status: isReady ? 'CONNECTED' : 'DISCONNECTED' });
});

app.get('/qr', (req, res) => {
    if (isReady) {
        return res.json({ status: 'CONNECTED', qr: null });
    }
    res.json({ status: 'DISCONNECTED', qr: qrDataUrl });
});

app.post('/logout', async (req, res) => {
    try {
        await client.logout();
        isReady = false;
        res.json({ success: true, message: 'Logged out successfully' });
    } catch (error) {
        console.error('Logout error:', error);
        res.status(500).json({ error: 'Failed to logout' });
    }
});

// Add anti-ban delay helper
const delay = ms => new Promise(res => setTimeout(res, ms));

app.post('/send', async (req, res) => {
    if (!isReady) {
        return res.status(400).json({ error: 'WhatsApp client is not connected' });
    }

    const { number, message } = req.body;
    if (!number || !message) {
        return res.status(400).json({ error: 'Missing number or message' });
    }

    try {
        // Format number correctly (whatsapp-web.js requires country code + number @c.us)
        // Ensure only digits
        let formattedNumber = number.toString().replace(/\D/g, '');
        if (formattedNumber.length === 10) {
            formattedNumber = '91' + formattedNumber; // Default to India (+91)
        }
        const chatId = `${formattedNumber}@c.us`;

        // Check if number is registered on WhatsApp
        const isRegistered = await client.isRegisteredUser(chatId);
        if (!isRegistered) {
            return res.status(400).json({ error: 'Number is not registered on WhatsApp' });
        }

        // Simulate human behavior
        console.log(`Sending to ${chatId}...`);
        const chat = await client.getChatById(chatId);

        await chat.sendStateTyping();
        // Dynamic delay based on message length (e.g. 30ms per character + 500ms baseline)
        const typingDelay = Math.min(2500, 500 + (message.length * 30));
        await delay(typingDelay);
        await chat.clearState();

        const response = await client.sendMessage(chatId, message);
        console.log(`Message sent successfully to ${number}`);
        res.json({ success: true, id: response.id._serialized });
    } catch (error) {
        console.error(`Failed to send message to ${number}:`, error);
        res.status(500).json({ error: error.toString() });
    }
});

app.listen(PORT, () => {
    console.log(`WhatsApp microservice running on port ${PORT}`);
});
