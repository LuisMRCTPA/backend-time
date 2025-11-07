const express = require('express');
const mongoose = require('mongoose')
const {MongoClient} = require('mongodb');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');  // Asegúrate de que esta línea esté presente
const bodyParser = require('body-parser');
const session = require('express-session'); // Agregar express-session
const cors = require('cors');




const app = express();
const uri = "mongodb://localhost:27017"; // Asegúrate de que la URL sea correcta para tu entorno
const client = new MongoClient(uri);
const dbName = 'SuperDB';
const secretKey = 'chayancito'; 
const Product = require('./models/Products')

mongoose.connect('mongodb://localhost:27017/SuperDB', {
    useNewUrlParser: true,
    useUnifiedTopology: true,
}).then(() =>console.log('conectado a MongoDB'))
.catch(err => console.error('Error al conectar a MongoDB', err));

app.use(bodyParser.json({limit: '10mb'}));
app.use(bodyParser.urlencoded({limit: '10mb', extended: true}))
app.use(cors({
    origin: 'http://127.0.0.1:5500',
    credentials: true
}));
 app.use(session({
    secret: secretKey,
    resave: false,
saveUninitialized: true,
cookie: {secure: false}
 }))

app.use(express.json()); // Para parsear JSON en las solicitudes

// Configuración de sesiones
app.use(session({
    secret: secretKey, // Puedes cambiar el secreto por algo más seguro
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false } // Cambiar a true si usas HTTPS
}));

app.post('/register', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json(
            { message: 'Por favor, '+
                'ingrese un usuario'+
               ' y contraseña válidos' });
    }

    try {
        await client.connect();
        const db = client.db(dbName);
        const usersCollection = db.collection('users');

        const userExists = 
        await usersCollection.findOne({ username });
        if (userExists) {
            return res.status(400).json(
                { message: 'El nombre de usuario ya está en uso' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const newUser = { username, password: hashedPassword };
        await usersCollection.insertOne(newUser);

        res.status(201).json(
            { message: 'Usuario registrado exitosamente' });
    } catch (error) {
        console.error('Error al registrar usuario:', error);
        res.status(500).json(
            { message: 'Error interno del servidor' });
    } finally {
        await client.close();
    }
});


app.post('/login', async (req,res) => {
    const {username, password} = req.body;
    if (!username || !password) {
        return res.status(400).json(
          {  message: 'Por Favor, ingrese'+
            'un usuario y contraseña validos'
    })
    }
    try {
        await  client.connect();
        const db = client.db(dbname)
        const usersCollection = db.Collection('users');
        const user = await usersCollection.findOne({username});
        if (!user) {
            return res.status(401).json(
                { message: 'Usuario no encontrado'});
        }
        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) {
            return res.status(401).json(
                { message: 'Contraseña incorrecta' });
        }
        req.session.user = {username: user,username, role: username === 'admin' ? 'admin' : 'user'};
        if (username === 'admin' && password === '1234' ) {
            return res.status(200).json({redirect: 'admin.html'})
        } else{
            return res.status(200).json({redirect: 'index.html'})
        }

    } catch (error) {
        console.error('Error al iniciar Sesion', error);
        res.status(500).json({ message: 'Error interno del sistema'})
    } finally {
        await client.close();
    }

});
app.get('/admin.html', (req,res) => {
    if (req.session.user && req.session.user.role === 'admin') {
            res.sendFile(path.join(__dirname, '../html/admin.html'));
    }else
            return res.status(400).json ({message: 'you are not allowed here BEGONE'})
            
        
})
app.post('/products',async (req,res) => {
    const { category, name, price, description, quantity, image } = req.body
    if ('!category || !name || !price|| !description || !quantity || !image'){
        return res.status(400).json(
            {message: 'Pls fill all the bits of info'});
    }
try { 
    await client.connect();
    const db = client.db(dbname);
    const productsCollection = db.collection('products');
    const newProduct = {
        category,
        name,
        price,
        description,
        quantity,
        image,
    };
    await productsCollection .insertOne(newProduct);
    res.status(201).json({message: 'produco agregado'});
} catch (error) {
    console.error('error al agregar producto', error);
    res.status(500).json ({
        message: 'error interno pls son try again we will cry'
    })
} finally {
    await client.close();
}
});
app.delete('/products/:id', async(req,res) => {
    const {id} = req.params;
    try {
        const result = await Product.findByIdAndDelete(id);
        if (!result) {
            return res.status(404).json({ message: 'Producto desaparecido'})
        }
        res.json({message: 'Producto Elimindao correctamente'});
    } catch(error) {
        console.error('error al eliminar producto', error);
    }
})
app.put('/products/:id', async (req, res) => {
    const {id} = req.params;
     try {
        const updatedProduct = await Product.findByIdAndDelete(id, req.body, {new: true});
        if (!updatedProduct) {
        return res.status(404).json({message: 'producto no encontrado'});
     }
     res.json(updatedProduct);
    } catch (error) {
        console.error('error al actualizar producto', error);
        res.status(500).json({message: 'error al actualizar producto'});
    }
});
const PORT = 3000;
app.listen(PORT, () => {
    console.log(`
        Servidor ejecutando
         en el puerto ${PORT}`);
    });