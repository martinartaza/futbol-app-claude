# E01-T8 - Backend en staging: notas

Ticket: [`requirements/0008-backend-staging.md`](../../requirements/0008-backend-staging.md),
tag `v0.1.8`.

## Alternativas y elección

- **ngrok o un servidor propio.** Hasta el 0007 las apps llegaban al backend local por
  un túnel de ngrok (servicio `ngrok` del compose, perfil `tunnel`). El túnel se cayó y
  dejó al usuario sin poder probar las apps. Como el usuario ya tiene un servidor en
  Hetzner con Traefik compartido, se eligió correr ahí el backend como **staging** y
  sacar ngrok: no depende de la máquina del desarrollador ni de un servicio externo.
- **Variables o nombres fijos para Traefik.** Primero se propusieron
  `TRAEFIK_NETWORK` y `TRAEFIK_CERT_RESOLVER` en el `.env`. El usuario mostró que en
  sus otros proyectos la red es siempre `traefik` y el resolver `letsencrypt`, así que
  quedaron fijos en los archivos de compose; en el `.env` solo va el dominio
  (`BACKEND_HOST`).
- **Un compose por entorno** (patrón de Docker "múltiples archivos de Compose"; The
  Twelve-Factor App, paridad dev/prod): `docker-compose.yml` es lo común,
  `compose.override.yml` lo de desarrollo (Compose lo carga solo) y
  `compose.staging.yml` lo del servidor. El label `tls.certresolver=letsencrypt` va
  solo en staging porque el Traefik local usa su certificado de mkcert y no tiene ese
  resolver.

## Instalación y configuración

- `backend/.env` del servidor: `APP_ENV=staging`, `BACKEND_HOST` (el dominio de
  staging), los `POSTGRES_*` con una contraseña fuerte y
  `COMPOSE_FILE=docker-compose.yml:compose.staging.yml`, para que cualquier
  `docker compose` en el servidor (`logs`, `ps`) no cargue el override de desarrollo.
- Despliegue: por ssh al servidor, en el clon del backend, `./tools/deploy.sh v0.1.8`.
  Baja el tag o la rama, corre `docker compose up -d --build --remove-orphans` y espera
  hasta 60 segundos a que `https://$BACKEND_HOST/health` responda 200. El script fija
  `COMPOSE_FILE` por su cuenta, por si el `.env` no lo tiene.
- Migraciones: el servicio `migrate` corre `alembic upgrade head` una vez; backend y
  worker esperan a que termine bien. En local también, así que el paso manual de
  `alembic upgrade head` ya no hace falta.
- Clientes (solo configuración): `backend.url` y `backend.url.release` en
  `android/local.properties`, `BACKEND_URL` en `ios/Config/Local.xcconfig` y en Vercel
  apuntan a `https://<host de staging>/graphql`.
- En el `.env` local sobran `COMPOSE_PROFILES`, `NGROK_AUTHTOKEN` y `NGROK_DOMAIN`.

## Problemas y soluciones

- **El chequeo del deploy fallaba aunque staging andaba.** Desde afuera `/health`
  respondía 200, pero en el servidor `curl` decía `Could not resolve host`: el servidor
  no resuelve su propio dominio. El script ahora usa `curl --resolve <host>:443:127.0.0.1`:
  la petición entra por el Traefik del servidor con TLS y el certificado real, sin DNS.
- **`/graphql` "no responde" en el navegador.** Es lo esperado: el navegador hace `GET`
  y fuera de local no hay GraphiQL (404). Las apps hacen `POST` con los headers de
  cliente, y eso responde.

## Otras notas

- Verificado en local: `docker compose up -d --build --remove-orphans` borró el
  contenedor de ngrok, `migrate` terminó con código 0 y `/health` respondió 200.
