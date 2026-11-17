# E01-T7 - Cierre de la E01: notas

Ticket: [`requirements/0007-close-e01.md`](../../requirements/0007-close-e01.md),
tag `v0.1.7`.

## Qué se corrió

- **Suite completa** (`tdd.py suite`) de backend, web, android, ios y workspace: todo en
  verde, sin regresiones.
- **`architecture-reviewer`** una vez sobre todo el diff de la épica: 15 hallazgos. El
  usuario aprobó corregir F-1 a F-11 en este ticket; F-12 a F-15 quedaron como preguntas
  abiertas de la E02 y la E04.
- **CI de iOS** (AC-9 del 0006): el primer `tests.yml` falló porque `macos-latest`
  (imagen `macos-26-arm64`) trae Xcode 26 y no tiene el simulador de iOS 27.2. Se pasó
  a la imagen `xcode-27` (preview de GitHub) eligiendo Xcode 27.2, el mismo build que en
  local, para que las snapshots coincidan. Quedó en `v0.1.7`; el tag `v0.1.6` no se
  movió porque el arreglo salió del cierre.

## Qué se corrigió

- **Tests del 0001** (F-1): el esqueleto del backend se había probado a mano.
  `backend/tests/test_backend_skeleton.py` corre la app en proceso con
  `httpx.ASGITransport` sobre la base de test: health 200 y 503, headers de cliente,
  version gate, settings con su caché, límite de profundidad, schema al día y cambio
  rompedor, y contratos de import-linter.
- **Stylelint en web** (F-2): reglas del núcleo de Stylelint, sin plugins: colores y
  largos solo con `var(--…)`, y nunca tokens primitivos. Se usó la versión 16 porque la
  18 pide Node 22.22 o más.
- **Tokens propios por componente** (F-3, F-4, F-5): grupo `message`, paddings de
  `coming-soon`, `nav`, `button` y `connection-gate`, y `nav.icon.size` para la
  campanita. Los valores no cambiaron, así que ninguna captura cambió.
- **Check `contracts`** en el workspace (F-6) y AC-10 del 0005 reescrito para apuntar a
  él (F-7).
- **Android por entradas** (F-8): `HealthNavigation.kt` y `AppConfigNavigation.kt` son
  lo único que la app usa de cada feature; la regla de Konsist ahora lo exige y tiene un
  fixture nuevo. "Actualizar" cae a la web de Play si no hay Play Store (F-11).
- **iOS**: el stub de los tests de UI solo existe en debug (F-9). La campanita pasó de
  la barra del sistema a una barra `Navigation` arriba, como en Android, y ahora se marca
  al elegirla (F-16, encontrado al probar a mano; el test de UI del 0006 lo verifica
  con permiso del usuario).
- **Web**: el BFF falla si falta `BUILD_NUMBER` en vez de mandar 1 (F-10).

## Release pipeline

La pregunta abierta de la épica se cerró así: en la E01 el bundle se arma en local y
se sube a mano a un track de prueba; armar y publicar desde CI quedó en la fila
"Releases" de `docs/production-readiness.md`.
