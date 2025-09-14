-- =====================================================
-- ESQUEMA COMPLETO DE BASE DE DATOS - ECOMMERCE APP
-- =====================================================
-- Generado automáticamente desde los modelos Django
-- Fecha: $(date)

-- =====================================================
-- TABLAS PRINCIPALES
-- =====================================================

-- Tabla: usuario
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_usuario VARCHAR(100) NOT NULL,
    apellido_usuario VARCHAR(100) NOT NULL,
    email_usuario VARCHAR(254) UNIQUE NOT NULL,
    telefono_usuario VARCHAR(15),
    direccion_usuario TEXT,
    fecha_nacimiento_usuario DATE,
    genero_usuario VARCHAR(10) CHECK (genero_usuario IN ('masculino', 'femenino', 'otro')),
    foto_perfil_usuario VARCHAR(100),
    estatus_usuario VARCHAR(10) DEFAULT 'activo' CHECK (estatus_usuario IN ('activo', 'inactivo')),
    fecha_creacion_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_usuario DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: empresa
CREATE TABLE empresa (
    id_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_empresa VARCHAR(200) NOT NULL,
    descripcion_empresa TEXT,
    email_empresa VARCHAR(254) UNIQUE NOT NULL,
    telefono_empresa VARCHAR(15),
    direccion_empresa TEXT,
    sitio_web_empresa VARCHAR(200),
    logo_empresa VARCHAR(100),
    ruc_empresa VARCHAR(20) UNIQUE,
    tipo_empresa VARCHAR(20) CHECK (tipo_empresa IN ('individual', 'sociedad', 'corporacion')),
    estatus_empresa VARCHAR(10) DEFAULT 'activo' CHECK (estatus_empresa IN ('activo', 'inactivo')),
    fecha_creacion_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_empresa DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: sucursal
CREATE TABLE sucursal (
    id_sucursal INTEGER PRIMARY KEY AUTO_INCREMENT,
    id_empresa_fk INTEGER NOT NULL,
    nombre_sucursal VARCHAR(200) NOT NULL,
    direccion_sucursal TEXT NOT NULL,
    telefono_sucursal VARCHAR(15),
    email_sucursal VARCHAR(254),
    horario_atencion VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    estatus_sucursal VARCHAR(10) DEFAULT 'activo' CHECK (estatus_sucursal IN ('activo', 'inactivo')),
    fecha_creacion_sucursal DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE
);

-- =====================================================
-- TABLAS DE CATEGORÍAS
-- =====================================================

-- Tabla: categoria_producto_empresa
CREATE TABLE categoria_producto_empresa (
    id_categoria_producto_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_categoria_producto_empresa VARCHAR(100) NOT NULL,
    descripcion_categoria_producto_empresa TEXT,
    estatus_categoria_producto_empresa VARCHAR(10) DEFAULT 'activo' CHECK (estatus_categoria_producto_empresa IN ('activo', 'inactivo')),
    fecha_creacion_categoria_producto_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_empresa_fk INTEGER NOT NULL,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE
);

-- Tabla: categoria_servicio_empresa
CREATE TABLE categoria_servicio_empresa (
    id_categoria_servicio_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_categoria_servicio_empresa VARCHAR(100) NOT NULL,
    descripcion_categoria_servicio_empresa TEXT,
    estatus_categoria_servicio_empresa VARCHAR(10) DEFAULT 'activo' CHECK (estatus_categoria_servicio_empresa IN ('activo', 'inactivo')),
    fecha_creacion_categoria_servicio_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_empresa_fk INTEGER NOT NULL,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE
);

-- Tabla: categoria_producto_usuario
CREATE TABLE categoria_producto_usuario (
    id_categoria_producto_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_categoria_producto_usuario VARCHAR(100) NOT NULL,
    descripcion_categoria_producto_usuario TEXT,
    estatus_categoria_producto_usuario VARCHAR(10) DEFAULT 'activo' CHECK (estatus_categoria_producto_usuario IN ('activo', 'inactivo')),
    fecha_creacion_categoria_producto_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario_fk INTEGER NOT NULL,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

-- Tabla: categoria_servicio_usuario
CREATE TABLE categoria_servicio_usuario (
    id_categoria_servicio_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_categoria_servicio_usuario VARCHAR(100) NOT NULL,
    descripcion_categoria_servicio_usuario TEXT,
    estatus_categoria_servicio_usuario VARCHAR(10) DEFAULT 'activo' CHECK (estatus_categoria_servicio_usuario IN ('activo', 'inactivo')),
    fecha_creacion_categoria_servicio_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario_fk INTEGER NOT NULL,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

-- =====================================================
-- TABLAS DE PRODUCTOS
-- =====================================================

-- Tabla: producto_empresa
CREATE TABLE producto_empresa (
    id_producto_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_producto_empresa VARCHAR(200) NOT NULL,
    descripcion_producto_empresa TEXT,
    precio_producto_empresa DECIMAL(10,2) NOT NULL,
    stock_producto_empresa INTEGER DEFAULT 0,
    sku_producto_empresa VARCHAR(50) UNIQUE,
    peso_producto_empresa DECIMAL(8,2),
    dimensiones_producto_empresa VARCHAR(100),
    marca_producto_empresa VARCHAR(100),
    modelo_producto_empresa VARCHAR(100),
    color_producto_empresa VARCHAR(50),
    material_producto_empresa VARCHAR(100),
    garantia_producto_empresa VARCHAR(200),
    estatus_producto_empresa VARCHAR(10) DEFAULT 'activo' CHECK (estatus_producto_empresa IN ('activo', 'inactivo')),
    fecha_creacion_producto_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_producto_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_categoria_fk INTEGER NOT NULL,
    id_empresa_fk INTEGER NOT NULL,
    FOREIGN KEY (id_categoria_fk) REFERENCES categoria_producto_empresa(id_categoria_producto_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE
);

-- Tabla: producto_usuario
CREATE TABLE producto_usuario (
    id_producto_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_producto_usuario VARCHAR(200) NOT NULL,
    descripcion_producto_usuario TEXT,
    precio_producto_usuario DECIMAL(10,2) NOT NULL,
    stock_producto_usuario INTEGER DEFAULT 0,
    sku_producto_usuario VARCHAR(50) UNIQUE,
    peso_producto_usuario DECIMAL(8,2),
    dimensiones_producto_usuario VARCHAR(100),
    marca_producto_usuario VARCHAR(100),
    modelo_producto_usuario VARCHAR(100),
    color_producto_usuario VARCHAR(50),
    material_producto_usuario VARCHAR(100),
    garantia_producto_usuario VARCHAR(200),
    estatus_producto_usuario VARCHAR(10) DEFAULT 'activo' CHECK (estatus_producto_usuario IN ('activo', 'inactivo')),
    fecha_creacion_producto_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_producto_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_categoria_fk INTEGER NOT NULL,
    id_usuario_fk INTEGER NOT NULL,
    FOREIGN KEY (id_categoria_fk) REFERENCES categoria_producto_usuario(id_categoria_producto_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

-- Tabla: producto_sucursal
CREATE TABLE producto_sucursal (
    id_producto_sucursal INTEGER PRIMARY KEY AUTO_INCREMENT,
    stock_sucursal INTEGER DEFAULT 0,
    precio_sucursal DECIMAL(10,2),
    disponible_sucursal BOOLEAN DEFAULT TRUE,
    fecha_actualizacion_stock DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_producto_fk INTEGER NOT NULL,
    id_sucursal_fk INTEGER NOT NULL,
    FOREIGN KEY (id_producto_fk) REFERENCES producto_empresa(id_producto_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_sucursal_fk) REFERENCES sucursal(id_sucursal) ON DELETE CASCADE,
    UNIQUE(id_producto_fk, id_sucursal_fk)
);

-- =====================================================
-- TABLAS DE SERVICIOS
-- =====================================================

-- Tabla: servicio_empresa
CREATE TABLE servicio_empresa (
    id_servicio_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_servicio_empresa VARCHAR(200) NOT NULL,
    descripcion_servicio_empresa TEXT,
    precio_base_servicio_empresa DECIMAL(10,2) NOT NULL,
    duracion_estimada_servicio_empresa INTEGER,
    tipo_precio_servicio_empresa VARCHAR(10) DEFAULT 'fijo' CHECK (tipo_precio_servicio_empresa IN ('fijo', 'por_hora', 'cotizacion')),
    disponible_servicio_empresa BOOLEAN DEFAULT TRUE,
    requisitos_servicio_empresa TEXT,
    estatus_servicio_empresa VARCHAR(10) DEFAULT 'activo' CHECK (estatus_servicio_empresa IN ('activo', 'inactivo')),
    fecha_creacion_servicio_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_servicio_empresa DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_categoria_fk INTEGER NOT NULL,
    id_empresa_fk INTEGER NOT NULL,
    FOREIGN KEY (id_categoria_fk) REFERENCES categoria_servicio_empresa(id_categoria_servicio_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE
);

-- Tabla: servicio_usuario
CREATE TABLE servicio_usuario (
    id_servicio_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre_servicio_usuario VARCHAR(200) NOT NULL,
    descripcion_servicio_usuario TEXT,
    precio_base_servicio_usuario DECIMAL(10,2) NOT NULL,
    duracion_estimada_servicio_usuario INTEGER,
    tipo_precio_servicio_usuario VARCHAR(10) DEFAULT 'fijo' CHECK (tipo_precio_servicio_usuario IN ('fijo', 'por_hora', 'cotizacion')),
    disponible_servicio_usuario BOOLEAN DEFAULT TRUE,
    requisitos_servicio_usuario TEXT,
    estatus_servicio_usuario VARCHAR(10) DEFAULT 'activo' CHECK (estatus_servicio_usuario IN ('activo', 'inactivo')),
    fecha_creacion_servicio_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion_servicio_usuario DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_categoria_fk INTEGER NOT NULL,
    id_usuario_fk INTEGER NOT NULL,
    FOREIGN KEY (id_categoria_fk) REFERENCES categoria_servicio_usuario(id_categoria_servicio_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

-- Tabla: servicio_sucursal
CREATE TABLE servicio_sucursal (
    id_servicio_sucursal INTEGER PRIMARY KEY AUTO_INCREMENT,
    precio_sucursal DECIMAL(10,2),
    disponible_sucursal BOOLEAN DEFAULT TRUE,
    capacidad_diaria INTEGER DEFAULT 1,
    horarios_disponibles TEXT,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_servicio_fk INTEGER NOT NULL,
    id_sucursal_fk INTEGER NOT NULL,
    FOREIGN KEY (id_servicio_fk) REFERENCES servicio_empresa(id_servicio_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_sucursal_fk) REFERENCES sucursal(id_sucursal) ON DELETE CASCADE,
    UNIQUE(id_servicio_fk, id_sucursal_fk)
);

-- =====================================================
-- TABLAS DE IMÁGENES
-- =====================================================

-- Tabla: imagen_producto_empresa
CREATE TABLE imagen_producto_empresa (
    id_imagen_producto_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    imagen_producto_empresa VARCHAR(100) NOT NULL,
    alt_text_imagen VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    orden_imagen INTEGER DEFAULT 0,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_producto_fk INTEGER NOT NULL,
    FOREIGN KEY (id_producto_fk) REFERENCES producto_empresa(id_producto_empresa) ON DELETE CASCADE
);

-- Tabla: imagen_servicio_empresa
CREATE TABLE imagen_servicio_empresa (
    id_imagen_servicio_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    imagen_servicio_empresa VARCHAR(100) NOT NULL,
    alt_text_imagen VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    orden_imagen INTEGER DEFAULT 0,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_servicio_fk INTEGER NOT NULL,
    FOREIGN KEY (id_servicio_fk) REFERENCES servicio_empresa(id_servicio_empresa) ON DELETE CASCADE
);

-- Tabla: imagen_producto_usuario
CREATE TABLE imagen_producto_usuario (
    id_imagen_producto_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    imagen_producto_usuario VARCHAR(100) NOT NULL,
    alt_text_imagen VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    orden_imagen INTEGER DEFAULT 0,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_producto_fk INTEGER NOT NULL,
    FOREIGN KEY (id_producto_fk) REFERENCES producto_usuario(id_producto_usuario) ON DELETE CASCADE
);

-- Tabla: imagen_servicio_usuario
CREATE TABLE imagen_servicio_usuario (
    id_imagen_servicio_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    imagen_servicio_usuario VARCHAR(100) NOT NULL,
    alt_text_imagen VARCHAR(200),
    es_principal BOOLEAN DEFAULT FALSE,
    orden_imagen INTEGER DEFAULT 0,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_servicio_fk INTEGER NOT NULL,
    FOREIGN KEY (id_servicio_fk) REFERENCES servicio_usuario(id_servicio_usuario) ON DELETE CASCADE
);

-- =====================================================
-- TABLAS DE CARRITO DE COMPRAS
-- =====================================================

-- Tabla: carrito_compra_producto_usuario
CREATE TABLE carrito_compra_producto_usuario (
    id_carrito_compra_producto_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    cantidad_carrito INTEGER NOT NULL,
    precio_unitario_carrito DECIMAL(10,2) NOT NULL,
    subtotal_carrito DECIMAL(10,2) NOT NULL,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario_fk INTEGER NOT NULL,
    idproducto_fk_usuario INTEGER,
    id_fk_producto_sucursal_empresa INTEGER,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (idproducto_fk_usuario) REFERENCES producto_usuario(id_producto_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_fk_producto_sucursal_empresa) REFERENCES producto_sucursal(id_producto_sucursal) ON DELETE SET NULL
);

-- Tabla: carrito_compra_producto_empresa
CREATE TABLE carrito_compra_producto_empresa (
    id_carrito_compra_producto_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    cantidad_carrito INTEGER NOT NULL,
    precio_unitario_carrito DECIMAL(10,2) NOT NULL,
    subtotal_carrito DECIMAL(10,2) NOT NULL,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_empresa_fk INTEGER NOT NULL,
    idproducto_fk_usuario INTEGER,
    id_fk_producto_sucursal_empresa INTEGER,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    FOREIGN KEY (idproducto_fk_usuario) REFERENCES producto_usuario(id_producto_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_fk_producto_sucursal_empresa) REFERENCES producto_sucursal(id_producto_sucursal) ON DELETE SET NULL
);

-- =====================================================
-- TABLAS DE PEDIDOS
-- =====================================================

-- Tabla: pedido_usuario
CREATE TABLE pedido_usuario (
    id_pedido_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    numero_pedido VARCHAR(20) UNIQUE NOT NULL,
    fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado_pedido VARCHAR(20) DEFAULT 'pendiente' CHECK (estado_pedido IN ('pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado')),
    total_pedido DECIMAL(10,2) NOT NULL,
    direccion_envio TEXT NOT NULL,
    metodo_pago VARCHAR(50) CHECK (metodo_pago IN ('tarjeta', 'transferencia', 'efectivo', 'paypal')),
    comprobante_pago VARCHAR(100),
    notas_pedido TEXT,
    comentario_rechazo TEXT,
    id_carrito_fk INTEGER NOT NULL,
    FOREIGN KEY (id_carrito_fk) REFERENCES carrito_compra_producto_usuario(id_carrito_compra_producto_usuario) ON DELETE CASCADE
);

-- Tabla: detalle_pedido_usuario
CREATE TABLE detalle_pedido_usuario (
    id_detalle_pedido_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    cantidad_detalle_pedido INTEGER NOT NULL,
    precio_unitario_pedido DECIMAL(10,2) NOT NULL,
    subtotal_detalle_pedido DECIMAL(10,2) NOT NULL,
    id_pedido_fk INTEGER NOT NULL,
    idproducto_fk_usuario INTEGER,
    id_fk_producto_sucursal_empresa INTEGER,
    FOREIGN KEY (id_pedido_fk) REFERENCES pedido_usuario(id_pedido_usuario) ON DELETE CASCADE,
    FOREIGN KEY (idproducto_fk_usuario) REFERENCES producto_usuario(id_producto_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_fk_producto_sucursal_empresa) REFERENCES producto_sucursal(id_producto_sucursal) ON DELETE SET NULL
);

-- Tabla: pedido_empresa
CREATE TABLE pedido_empresa (
    id_pedido_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    numero_pedido VARCHAR(20) UNIQUE NOT NULL,
    fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado_pedido VARCHAR(20) DEFAULT 'pendiente' CHECK (estado_pedido IN ('pendiente', 'confirmado', 'enviado', 'entregado', 'cancelado')),
    total_pedido DECIMAL(10,2) NOT NULL,
    direccion_envio TEXT NOT NULL,
    metodo_pago VARCHAR(50) CHECK (metodo_pago IN ('tarjeta', 'transferencia', 'efectivo', 'paypal')),
    comprobante_pago VARCHAR(100),
    notas_pedido TEXT,
    comentario_rechazo TEXT,
    id_carrito_fk INTEGER NOT NULL,
    FOREIGN KEY (id_carrito_fk) REFERENCES carrito_compra_producto_empresa(id_carrito_compra_producto_empresa) ON DELETE CASCADE
);

-- Tabla: detalle_pedido_empresa
CREATE TABLE detalle_pedido_empresa (
    id_detalle_pedido_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    cantidad_detalle_pedido INTEGER NOT NULL,
    precio_unitario_pedido DECIMAL(10,2) NOT NULL,
    subtotal_detalle_pedido DECIMAL(10,2) NOT NULL,
    id_pedido_fk INTEGER NOT NULL,
    idproducto_fk_usuario INTEGER,
    id_fk_producto_sucursal_empresa INTEGER,
    FOREIGN KEY (id_pedido_fk) REFERENCES pedido_empresa(id_pedido_empresa) ON DELETE CASCADE,
    FOREIGN KEY (idproducto_fk_usuario) REFERENCES producto_usuario(id_producto_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_fk_producto_sucursal_empresa) REFERENCES producto_sucursal(id_producto_sucursal) ON DELETE SET NULL
);

-- =====================================================
-- TABLAS DE SOLICITUDES DE SERVICIOS
-- =====================================================

-- Tabla: solicitud_servicio_usuario
CREATE TABLE solicitud_servicio_usuario (
    id_solicitud_servicio_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_requerida DATE NOT NULL,
    direccion TEXT NOT NULL,
    descripcion_detallada TEXT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'cotizada', 'aceptada', 'pagada', 'completada', 'rechazada')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario_fk INTEGER NOT NULL,
    id_servicio_usuario_fk INTEGER,
    id_servicio_sucursal_fk INTEGER,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_usuario_fk) REFERENCES servicio_usuario(id_servicio_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_sucursal_fk) REFERENCES servicio_sucursal(id_servicio_sucursal) ON DELETE CASCADE
);

-- Tabla: solicitud_servicio_empresa
CREATE TABLE solicitud_servicio_empresa (
    id_solicitud_servicio_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    fecha_solicitud DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_requerida DATE NOT NULL,
    direccion TEXT NOT NULL,
    descripcion_detallada TEXT NOT NULL,
    estado VARCHAR(20) DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'cotizada', 'aceptada', 'pagada', 'completada', 'rechazada')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_empresa_fk INTEGER NOT NULL,
    id_servicio_usuario_fk INTEGER,
    id_servicio_sucursal_fk INTEGER,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_usuario_fk) REFERENCES servicio_usuario(id_servicio_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_sucursal_fk) REFERENCES servicio_sucursal(id_servicio_sucursal) ON DELETE CASCADE
);

-- =====================================================
-- TABLAS DE NOTIFICACIONES
-- =====================================================

-- Tabla: notificacion_usuario
CREATE TABLE notificacion_usuario (
    id_notificacion_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    tipo_notificacion VARCHAR(20) CHECK (tipo_notificacion IN ('pedido_confirmado', 'pedido_rechazado', 'pedido_enviado', 'pedido_entregado', 'servicio_cotizado', 'servicio_aceptado', 'servicio_completado')),
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(10) DEFAULT 'no_leida' CHECK (estado IN ('no_leida', 'leida')),
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_leida DATETIME,
    id_usuario_fk INTEGER NOT NULL,
    id_pedido_usuario_fk INTEGER,
    id_solicitud_servicio_usuario_fk INTEGER,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_pedido_usuario_fk) REFERENCES pedido_usuario(id_pedido_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_solicitud_servicio_usuario_fk) REFERENCES solicitud_servicio_usuario(id_solicitud_servicio_usuario) ON DELETE CASCADE
);

-- Tabla: notificacion_empresa
CREATE TABLE notificacion_empresa (
    id_notificacion_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    tipo_notificacion VARCHAR(20) CHECK (tipo_notificacion IN ('venta_pendiente', 'venta_confirmada', 'venta_rechazada', 'nuevo_pedido', 'solicitud_servicio', 'servicio_pagado')),
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    estado VARCHAR(10) DEFAULT 'no_leida' CHECK (estado IN ('no_leida', 'leida')),
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_leida DATETIME,
    id_empresa_fk INTEGER NOT NULL,
    id_pedido_empresa_fk INTEGER,
    id_solicitud_servicio_empresa_fk INTEGER,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_pedido_empresa_fk) REFERENCES pedido_empresa(id_pedido_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_solicitud_servicio_empresa_fk) REFERENCES solicitud_servicio_empresa(id_solicitud_servicio_empresa) ON DELETE CASCADE
);

-- =====================================================
-- TABLAS DE FAVORITOS
-- =====================================================

-- Tabla: favoritos_usuarios
CREATE TABLE favoritos_usuarios (
    id_favorito_usuario INTEGER PRIMARY KEY AUTO_INCREMENT,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_usuario_fk INTEGER NOT NULL,
    id_producto_usuario_fk INTEGER,
    id_producto_sucursal_fk INTEGER,
    id_servicio_usuario_fk INTEGER,
    id_servicio_sucursal_fk INTEGER,
    FOREIGN KEY (id_usuario_fk) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_producto_usuario_fk) REFERENCES producto_usuario(id_producto_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_producto_sucursal_fk) REFERENCES producto_sucursal(id_producto_sucursal) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_usuario_fk) REFERENCES servicio_usuario(id_servicio_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_sucursal_fk) REFERENCES servicio_sucursal(id_servicio_sucursal) ON DELETE CASCADE,
    UNIQUE(id_usuario_fk, id_producto_usuario_fk),
    UNIQUE(id_usuario_fk, id_producto_sucursal_fk),
    UNIQUE(id_usuario_fk, id_servicio_usuario_fk),
    UNIQUE(id_usuario_fk, id_servicio_sucursal_fk)
);

-- Tabla: favoritos_empresas
CREATE TABLE favoritos_empresas (
    id_favorito_empresa INTEGER PRIMARY KEY AUTO_INCREMENT,
    fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_empresa_fk INTEGER NOT NULL,
    id_producto_usuario_fk INTEGER,
    id_servicio_usuario_fk INTEGER,
    FOREIGN KEY (id_empresa_fk) REFERENCES empresa(id_empresa) ON DELETE CASCADE,
    FOREIGN KEY (id_producto_usuario_fk) REFERENCES producto_usuario(id_producto_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_servicio_usuario_fk) REFERENCES servicio_usuario(id_servicio_usuario) ON DELETE CASCADE,
    UNIQUE(id_empresa_fk, id_producto_usuario_fk),
    UNIQUE(id_empresa_fk, id_servicio_usuario_fk)
);

-- =====================================================
-- SISTEMA EAV (Entity-Attribute-Value)
-- =====================================================

-- Tabla: AtributoProducto
CREATE TABLE AtributoProducto (
    id_atributo INTEGER PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    tipo_dato VARCHAR(20) CHECK (tipo_dato IN ('texto', 'numero', 'decimal', 'fecha', 'booleano', 'lista')),
    opciones TEXT, -- JSON field para opciones de lista
    obligatorio BOOLEAN DEFAULT FALSE,
    descripcion TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: CategoriaAtributo (Tabla intermedia)
CREATE TABLE CategoriaAtributo (
    id_categoria_atributo INTEGER PRIMARY KEY AUTO_INCREMENT,
    orden INTEGER DEFAULT 0,
    fecha_asociacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    atributo_id INTEGER NOT NULL,
    categoria_usuario_id INTEGER,
    categoria_empresa_id INTEGER,
    FOREIGN KEY (atributo_id) REFERENCES AtributoProducto(id_atributo) ON DELETE CASCADE,
    FOREIGN KEY (categoria_usuario_id) REFERENCES categoria_producto_usuario(id_categoria_producto_usuario) ON DELETE CASCADE,
    FOREIGN KEY (categoria_empresa_id) REFERENCES categoria_producto_empresa(id_categoria_producto_empresa) ON DELETE CASCADE,
    UNIQUE(atributo_id, categoria_usuario_id),
    UNIQUE(atributo_id, categoria_empresa_id),
    CHECK ((categoria_usuario_id IS NOT NULL AND categoria_empresa_id IS NULL) OR 
           (categoria_usuario_id IS NULL AND categoria_empresa_id IS NOT NULL))
);

-- Tabla: ValorAtributoProducto
CREATE TABLE ValorAtributoProducto (
    id_valor_atributo INTEGER PRIMARY KEY AUTO_INCREMENT,
    valor_texto TEXT,
    valor_numero INTEGER,
    valor_decimal DECIMAL(10,2),
    valor_fecha DATE,
    valor_booleano BOOLEAN,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    producto_usuario_id INTEGER,
    producto_empresa_id INTEGER,
    atributo_id INTEGER NOT NULL,
    FOREIGN KEY (producto_usuario_id) REFERENCES producto_usuario(id_producto_usuario) ON DELETE CASCADE,
    FOREIGN KEY (producto_empresa_id) REFERENCES producto_empresa(id_producto_empresa) ON DELETE CASCADE,
    FOREIGN KEY (atributo_id) REFERENCES AtributoProducto(id_atributo) ON DELETE CASCADE,
    UNIQUE(producto_usuario_id, atributo_id),
    UNIQUE(producto_empresa_id, atributo_id),
    CHECK ((producto_usuario_id IS NOT NULL AND producto_empresa_id IS NULL) OR 
           (producto_usuario_id IS NULL AND producto_empresa_id IS NOT NULL))
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN DE RENDIMIENTO
-- =====================================================

-- Índices para categorías y productos
CREATE INDEX idx_producto_empresa_categoria ON producto_empresa(id_categoria_fk);
CREATE INDEX idx_producto_usuario_categoria ON producto_usuario(id_categoria_fk);
CREATE INDEX idx_servicio_empresa_categoria ON servicio_empresa(id_categoria_fk);
CREATE INDEX idx_servicio_usuario_categoria ON servicio_usuario(id_categoria_fk);

-- Índices para fechas y estados
CREATE INDEX idx_pedido_usuario_fecha ON pedido_usuario(fecha_pedido);
CREATE INDEX idx_pedido_empresa_fecha ON pedido_empresa(fecha_pedido);
CREATE INDEX idx_pedido_usuario_estado ON pedido_usuario(estado_pedido);
CREATE INDEX idx_pedido_empresa_estado ON pedido_empresa(estado_pedido);

-- Índices para notificaciones
CREATE INDEX idx_notificacion_usuario_estado ON notificacion_usuario(estado, fecha_creacion);
CREATE INDEX idx_notificacion_empresa_estado ON notificacion_empresa(estado, fecha_creacion);

-- Índices para estatus de productos y servicios
CREATE INDEX idx_producto_empresa_estatus ON producto_empresa(estatus_producto_empresa);
CREATE INDEX idx_producto_usuario_estatus ON producto_usuario(estatus_producto_usuario);
CREATE INDEX idx_servicio_empresa_estatus ON servicio_empresa(estatus_servicio_empresa);
CREATE INDEX idx_servicio_usuario_estatus ON servicio_usuario(estatus_servicio_usuario);

-- Índices para búsquedas por email
CREATE INDEX idx_usuario_email ON usuario(email_usuario);
CREATE INDEX idx_empresa_email ON empresa(email_empresa);

-- Índices para carritos y favoritos
CREATE INDEX idx_carrito_usuario_fecha ON carrito_compra_producto_usuario(fecha_agregado);
CREATE INDEX idx_carrito_empresa_fecha ON carrito_compra_producto_empresa(fecha_agregado);
CREATE INDEX idx_favoritos_usuario_fecha ON favoritos_usuarios(fecha_agregado);
CREATE INDEX idx_favoritos_empresa_fecha ON favoritos_empresas(fecha_agregado);

-- Índices para sistema EAV
CREATE INDEX idx_valor_atributo_producto_usuario ON ValorAtributoProducto(producto_usuario_id);
CREATE INDEX idx_valor_atributo_producto_empresa ON ValorAtributoProducto(producto_empresa_id);
CREATE INDEX idx_valor_atributo_atributo ON ValorAtributoProducto(atributo_id);
CREATE INDEX idx_categoria_atributo_categoria_usuario ON CategoriaAtributo(categoria_usuario_id);
CREATE INDEX idx_categoria_atributo_categoria_empresa ON CategoriaAtributo(categoria_empresa_id);

-- =====================================================
-- DATOS DE EJEMPLO (OPCIONAL)
-- =====================================================

-- Insertar algunos atributos básicos para productos
INSERT INTO AtributoProducto (nombre, tipo_dato, descripcion, obligatorio) VALUES
('Marca', 'texto', 'Marca del producto', TRUE),
('Modelo', 'texto', 'Modelo del producto', FALSE),
('Color', 'lista', 'Color disponible del producto', FALSE),
('Peso', 'decimal', 'Peso del producto en kilogramos', FALSE),
('Garantía', 'numero', 'Meses de garantía', FALSE),
('Nuevo/Usado', 'lista', 'Estado del producto', TRUE),
('Procesador', 'texto', 'Tipo de procesador (para electrónicos)', FALSE),
('RAM', 'numero', 'Memoria RAM en GB (para computadoras)', FALSE),
('Almacenamiento', 'numero', 'Capacidad de almacenamiento en GB', FALSE),
('Pantalla', 'decimal', 'Tamaño de pantalla en pulgadas', FALSE);

-- Actualizar opciones para atributos de tipo lista
UPDATE AtributoProducto SET opciones = '["Rojo", "Azul", "Verde", "Negro", "Blanco", "Gris", "Amarillo", "Rosa", "Morado", "Naranja"]' WHERE nombre = 'Color';
UPDATE AtributoProducto SET opciones = '["Nuevo", "Usado - Como Nuevo", "Usado - Buen Estado", "Usado - Estado Regular"]' WHERE nombre = 'Nuevo/Usado';

-- =====================================================
-- COMENTARIOS FINALES
-- =====================================================

/*
ESTE ESQUEMA INCLUYE:

1. **32 TABLAS PRINCIPALES** con todas sus relaciones y constraints
2. **SISTEMA EAV** para atributos dinámicos de productos
3. **ÍNDICES OPTIMIZADOS** para mejorar el rendimiento
4. **CONSTRAINTS Y VALIDACIONES** para integridad de datos
5. **DATOS DE EJEMPLO** para atributos básicos

PARA USAR ESTE ARCHIVO:
1. Ejecuta este script en tu base de datos SQLite/PostgreSQL/MySQL
2. Ajusta los tipos de datos según tu motor de base de datos
3. Modifica las opciones de atributos según tus necesidades
4. Agrega más datos de ejemplo si es necesario

NOTA: Este esquema está basado en los modelos Django del proyecto
y mantiene la compatibilidad con el ORM de Django.
*/