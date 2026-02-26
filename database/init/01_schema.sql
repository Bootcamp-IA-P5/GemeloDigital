-- MVP Gemelo Digital - Esquema Inicial de Base de Datos

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tabla Usuario
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    rol_sistema VARCHAR(50) DEFAULT 'USER',
    rol_profesional_actual VARCHAR(255),
    nivel_experiencia VARCHAR(50),
    objetivo_profesional TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla Competencia
CREATE TABLE IF NOT EXISTS competencias (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    categoria VARCHAR(100), -- HARD_SKILL, SOFT_SKILL
    descripcion TEXT
);

-- Tabla intermedia (Gemelo del Usuario)
CREATE TABLE IF NOT EXISTS perfil_competencia (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    competencia_id UUID REFERENCES competencias(id) ON DELETE CASCADE,
    nivel_actual INTEGER CHECK (nivel_actual >= 1 AND nivel_actual <= 5),
    nivel_objetivo INTEGER CHECK (nivel_objetivo >= 1 AND nivel_objetivo <= 5),
    UNIQUE(usuario_id, competencia_id)
);

-- 3. Tabla Contenido (Catálogo)
CREATE TABLE IF NOT EXISTS contenidos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo VARCHAR(255) NOT NULL,
    tipo VARCHAR(100), -- CURSO, TALLER, ARTICULO
    descripcion TEXT,
    duracion_horas INTEGER
);

-- Tabla intermedia (Competencias asociadas al contenido)
CREATE TABLE IF NOT EXISTS contenido_competencia (
    contenido_id UUID REFERENCES contenidos(id) ON DELETE CASCADE,
    competencia_id UUID REFERENCES competencias(id) ON DELETE CASCADE,
    impacto INTEGER, -- Ej. +1 al nivel de competencia
    PRIMARY KEY(contenido_id, competencia_id)
);

-- 4. Tabla Roadmap
CREATE TABLE IF NOT EXISTS roadmaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(50) DEFAULT 'ACTIVO',
    enfoque VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS fases_roadmap (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    titulo VARCHAR(255),
    objetivo_fase TEXT
);

CREATE TABLE IF NOT EXISTS bloques_aprendizaje (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fase_id UUID REFERENCES fases_roadmap(id) ON DELETE CASCADE,
    contenido_id UUID REFERENCES contenidos(id) ON DELETE SET NULL,
    orden INTEGER NOT NULL,
    justificacion_pedagogica TEXT
);

-- 5. Tabla Progreso
CREATE TABLE IF NOT EXISTS progresos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    bloque_aprendizaje_id UUID REFERENCES bloques_aprendizaje(id) ON DELETE CASCADE,
    estado VARCHAR(50) DEFAULT 'PENDIENTE',
    fecha_completado TIMESTAMP,
    UNIQUE(usuario_id, bloque_aprendizaje_id)
);
