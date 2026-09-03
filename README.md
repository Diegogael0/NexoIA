# Nexo IA V4.2.2 — Usuarios, empresas y permisos

Esta versión conserva el diseño y funciones de V4.1 y agrega autenticación real con API.

## Administrador general
- Usuario: `admin`
- Correo alterno: `admin@nexoia.mx`
- Contraseña temporal: `12345678`

> Esta contraseña es solo para pruebas locales. Cámbiala antes de publicar la aplicación.

## Qué puede hacer el administrador
- Ver `Mis empresas`.
- Crear empresas.
- Ver `Usuarios y permisos`.
- Crear un usuario para una empresa específica.
- Elegir exactamente qué módulos puede ver ese usuario.
- Bloquear o reactivar usuarios.
- Ver todos los menús.

## Qué ve un usuario de empresa
- No ve `Mis empresas`.
- No ve `Usuarios y permisos`.
- Solo queda asociado a su empresa.
- Solo aparecen los módulos que el administrador le autorizó.
- La API también valida que no pueda consultar otra empresa aunque intente modificar la URL.

## Ejecutar en Mac
No abras `file://.../index.html` para esta versión porque el login usa la API.

```bash
cd ~/Downloads/NexoIA_V4_2_Usuarios_Permisos
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up
```

Abre:
- Aplicación: http://localhost:8080
- API health: http://localhost:8000/health
- Swagger: http://localhost:8000/docs

## Importante sobre publicación
Netlify puede alojar el frontend, pero esta versión también necesita publicar la API y PostgreSQL.
Antes de subirla a Internet hay que:
1. Cambiar JWT_SECRET.
2. Cambiar la contraseña inicial del administrador.
3. Publicar API + PostgreSQL (por ejemplo Render/Railway/Fly.io u otro servidor).
4. Apuntar `API` del frontend a esa URL.
5. Configurar CORS con el dominio público.

## Estado actual de los datos operativos
La autenticación, empresas, usuarios y permisos están en PostgreSQL.
Los datos de agenda del prototipo V4.1 siguen guardándose localmente por empresa en el navegador.
El siguiente paso recomendado es mover también agenda, clientes, personal, servicios, horarios y bloqueos a PostgreSQL para que todos los dispositivos de una empresa compartan la misma información.


## Login simplificado para pruebas
En esta versión el acceso de administrador se fuerza en cada arranque:
- Usuario: `admin`
- Contraseña: `12345678`

Si había una contraseña anterior en PostgreSQL, el sistema la reemplaza automáticamente al iniciar la API.
La pantalla de login pide únicamente **Usuario** y **Contraseña**.


## V4.2.3 - Corrección API
Se corrigió el error:

`ImportError: email-validator is not installed`

La dependencia `email-validator==2.2.0` ya viene incluida en `backend/requirements.txt`.


## V4.2.4 — Corrección de navegación
Se corrigió el problema donde el administrador podía iniciar sesión pero los menús no respondían.

Causa: los botones estaban enlazados a `showView(...)`, pero esa función no estaba presente en el JavaScript final.

Ahora:
- El administrador puede abrir todos los menús.
- `Mis empresas` y `Usuarios y permisos` funcionan incluso antes de crear una empresa.
- Los usuarios de empresa siguen viendo únicamente los módulos autorizados.


## V4.2.5 — Usuarios y cuenta de administrador
Correcciones:
- Crear usuario ahora valida los campos antes de enviar.
- La contraseña de usuarios exige 8 caracteres y muestra el error dentro del modal.
- Los errores 422 de la API ahora se muestran de forma entendible.
- El botón cambia a `Creando...` mientras trabaja.
- Se agregó en Configuración un panel `Cuenta de administrador`.
- El administrador puede cambiar nombre, usuario, correo y contraseña.
- La contraseña del administrador ya NO se restablece a `12345678` en cada reinicio.
- `12345678` queda únicamente como contraseña inicial al crear por primera vez la base.


## V4.2.6 — Corrección definitiva de Crear usuario
Se encontró la causa exacta:

`app.js` se estaba cargando antes de que el modal `userAdminModal` existiera en el DOM.

Por eso:
- El botón `+ Crear usuario` sí abría el modal.
- Pero `Crear usuario` dentro del modal no tenía evento asociado.
- En los logs de API no aparecía ningún `POST /admin/users`.

Se movió `app.js` al final del documento, después de todos los modales.
Ahora el botón `Crear usuario` sí ejecuta `POST /admin/users`.


## V4.2.7 — Crear usuario robusto
Se reemplazó el botón por un formulario HTML real (`companyUserForm`) con evento `submit`.
Además se agregó un segundo mecanismo delegado como respaldo.

Al pulsar Crear usuario ahora debe verse inmediatamente:
- `Validando datos...`
- `Enviando usuario al servidor...`
- o un error visible dentro del modal.

Esto permite saber de inmediato si el clic está siendo procesado.


## V4.2.8 — Corrección `toast is not a function`
Se corrigió el error mostrado al crear usuarios:

`Error: toast is not a function`

Cambios:
- Se renombró el helper visual a `showToast(...)` para evitar conflictos.
- Los datos del formulario solo se borran después de que:
  1. la API cree el usuario correctamente, y
  2. la lista de usuarios se actualice correctamente.
- Si ocurre cualquier error, los campos permanecen llenos para poder corregir y reintentar.


## V4.2.9 — Notificaciones corregidas
Se corrigió `showToast is not defined`.

Ahora existe una función real `showToast(...)` y todas las notificaciones del sistema usan esa misma función.

Si el intento anterior alcanzó a crear el usuario antes de fallar la notificación,
al repetir el mismo usuario/correo puede aparecer `ya existe`. Revisa la tabla de usuarios
o usa otro usuario/correo para la prueba.


## V4.3 — Operación, usuarios, agenda y personal

Cambios principales:
- Usuarios de empresa ahora tienen botón **Editar**.
- Se puede cambiar nombre, usuario, correo, empresa, rol, permisos y contraseña.
- La contraseña es opcional al editar.
- **Nueva cita** ya no aparece en todos los módulos: solo Dashboard, Agenda, Disponibilidad y Citas.
- **Checador** solo aparece en Dashboard, Agenda y Personal.
- Agenda:
  - filtro por colaborador;
  - mantiene vista diaria por columnas;
  - clic en un espacio `Disponible` abre Nueva cita con colaborador, fecha y hora precargados.
- Personal:
  - nuevo botón **+ Agregar personal**;
  - nombre, alias, puesto, estado y servicios;
  - botón Editar en cada tarjeta;
  - después se pueden configurar horario y descansos como antes.


## V4.3.1 — Empresas limpias
Corrección importante:
- Las empresas nuevas ya NO heredan los servicios, clientes, personal ni citas de demostración.
- Cada empresa nueva inicia completamente vacía.
- En Personal, si todavía no existen servicios, ya no aparecen `Corte`, `Barba`, etc.
- En su lugar aparece: `Aún no hay servicios creados` + botón `Ir a Servicios`.
- Después de crear servicios, al editar/agregar personal sí aparecen para asignarlos.

Nota:
Si una empresa ya había guardado datos de prueba en localStorage, esos datos pueden seguir ahí.
Para probar una empresa totalmente limpia, crea una empresa nueva o limpia los datos locales de esa empresa.
