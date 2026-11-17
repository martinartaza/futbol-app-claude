# E01-T5 - Esqueleto Android: notas

Ticket: [`requirements/0005-android-skeleton.md`](../../requirements/0005-android-skeleton.md),
tag `v0.1.5`.

## Alternativas y elección

- **Cómo llega la app al backend local.** Se habló de `10.0.2.2` (el alias de la Mac
  en el emulador) con resolución de nombre y confianza en la CA de mkcert solo en debug.
  El usuario eligió ngrok: le dio problemas `10.0.2.2` en el proyecto anterior, sirve
  igual para un celular físico y el certificado es público. La seguridad no le preocupa
  (no hay datos reales).
- **El túnel como contenedor.** En lugar de abrirlo a mano, es un servicio `ngrok` del
  compose local del backend, con el perfil `tunnel` (Compose profiles) y el dominio fijo
  gratis del usuario; `backend.url` no cambia más. Un solo compose de local; producción
  tendrá su propia definición cuando se decida dónde corre.
- **`minSdk` 26.** El emulador del usuario es API 36; se explicó que `minSdk` es el
  mínimo aceptado y no el de prueba, y el usuario aceptó 26.
- **Firma.** El usuario tenía de la app anterior `key.properties` (formato Flutter) y la
  clave; se guardan en `secrets/` y el build lee `secrets/key.properties`. El usuario
  verificó con `keytool` que el SHA-1 de la clave coincide con el certificado de subida.

## Instalación y configuración

- Gradle 9.9.1 descargado al scratchpad solo para generar el wrapper
  (`gradle wrapper`); después todo corre con `./gradlew`.
- Versiones: AGP 9.5.1 (Kotlin integrado), Kotlin 2.4.21, KSP 2.3.14, Compose BOM
  2026.09.00, Hilt 2.60.1, Navigation Compose 2.10.2, Apollo Kotlin 5.2.0, OkHttp 5.5.1,
  Robolectric 4.18, Roborazzi 1.79.0, Konsist 0.18.1, detekt 1.23.8.
- `compileSdk` 37.2: las bibliotecas de AndroidX (`hilt-navigation-compose` 1.4) lo
  exigen; se instaló `platforms;android-37.2` con `sdkmanager`. `targetSdk` sigue en 36.
- `android/local.properties` (no se sube): `sdk.dir` y
  `backend.url=https://<NGROK_DOMAIN>/graphql`.
- `backend/.env`: `COMPOSE_PROFILES=tunnel`, `NGROK_AUTHTOKEN`, `NGROK_DOMAIN` (los
  cargó el usuario).
- Ícono: ver "Otras notas".

## Problemas y soluciones

- **El guard no deja copiar el schema a mano** al proyecto Android: lo copia
  `sync_contracts.py` (parte del 0005). El bloque de Apollo se configura en el TDD.
- **detekt 1.23 corre con Kotlin 2.0.21**: su configuración fuerza esa versión; el
  módulo de reglas se compila con `apiVersion` y `languageVersion` 2.0 para que detekt
  lo cargue. Forzar la versión en todo el módulo rompía la compilación (no existe
  `kotlin-build-tools-compat` 2.0.21).
- **El build de release sin configuración** falla antes de compilar, nombrando lo que
  falta (`secrets/key.properties` o una de sus claves, `backend.url.release`).
- Verificado: `bundleRelease` genera el AAB firmado con SHA-1
  `28:C8:54:03:...:01:FE`; el túnel del compose responde `health: ok` por el dominio
  fijo.

## Otras notas

- **Ícono**: el logo de la app anterior (versión de 1024 px de iOS) como ícono adaptativo: frente generado en los 5 tamaños (`mipmap-*/ic_launcher_foreground.png`, el logo al 64 %) y fondo blanco, así ocupa la forma de cada teléfono sin recortar el texto. El ícono de 512 px de Play Store se sube aparte en Play Console.
- El usuario instaló la app en el emulador y dio el andamiaje por terminado el 2026-11-15.

## Implementación del 0005 (TDD)

- **Tokens de Compose.** `sync_contracts.py` genera `Tokens.kt`: una `data class Tokens`
  con una propiedad tipada por token (`Color`, `Dp`, `FontWeight`, `String`) en camelCase
  y las instancias `whiteTokens` y `darkTokens`. `AppTheme` elige una según el sistema y
  la expone en `AppTheme.tokens`; los tamaños de texto se pasan de `Dp` a `sp`.
- **Inter.** Android no lee `woff2`: el `woff2` de la web se convirtió a `res/font/inter.ttf`
  con fontTools. Es una fuente variable; cada peso se pide con `FontVariation`.
- **Red.** Un solo cliente Apollo (`core/network`) con los headers `X-Client-Platform` y
  `X-Client-Version` y un interceptor que abre el `VersionGate` ante `UPGRADE_REQUIRED`.
  Hilt lo provee con `BuildConfig.BACKEND_URL` y `VERSION_CODE`.
- **Cáscara.** La campana va en una barra superior y las cinco secciones en la inferior:
  seis ítems no entraban en el ancho del teléfono (se vio en la primera captura de
  Roborazzi).
- **Reglas de detekt.** `NoFunctionBodyComments` (acepta KDoc y el ejemplo de una regex) y
  `NoLiteralDesignValues` (`Color(0x...)`, `16.dp`, `14.sp`), excluidas en los tests y en
  el archivo generado.
- **Problemas y soluciones.**
  - En Apollo 5 `ApolloException` es sellada; el usuario autorizó usar
    `ApolloNetworkException` en el test. También autorizó que el test de navegación haga
    click en el ítem de la barra y busque el título como encabezado (el texto se repetía).
  - Robolectric pide Java 21 para Android 36: los tests corren con JDK 21 descargado por
    Gradle (plugin Foojay); la compilación sigue en 17. En CI `tests.yml` instala 17 y 21.
  - El texto de los botones tomaba el color de la tipografía en vez del token del botón:
    la tipografía ya no fija color.
- Verificado a mano: la app en el emulador contra el backend real por ngrok muestra Inicio.
- **Guardia de reutilización.** El usuario preguntó si corrían hooks para no crear
  componentes sin buscar antes. El hook existía (`guard_edit.py`), pero ningún proyecto
  tenía `reuse_guard` en `workflow.json`: faltó en los esqueletos de web y Android. Se
  agregó a los dos y se probó que frena el primer intento de crear un archivo en `ui/`
  listando los parecidos. El revisor de arquitectura ahora verifica que cada regla que
  una skill dice controlada por una herramienta esté configurada. iOS lo suma en su
  esqueleto, cuando exista su entrada en `workflow.json`.
