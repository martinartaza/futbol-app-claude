# E01-T6 - Esqueleto iOS: notas

Ticket: [`requirements/0006-ios-skeleton.md`](../../requirements/0006-ios-skeleton.md),
tag `v0.1.6`.

## Alternativas y elección

- **Proyecto de Xcode.** Se comparó el `.xcodeproj` de Xcode (con carpetas
  sincronizadas) contra describirlo en texto con XcodeGen. Se eligió XcodeGen: el
  `project.yml` es corto y legible, el `.xcodeproj` se genera y no se sube, y no hay
  conflictos de git en el archivo de proyecto.
- **Reglas propias de lint.** Las reglas propias de SwiftLint son expresiones regulares y
  no distinguen un comentario dentro de una función de uno arriba de ella. Se eligió un
  paquete chico, `ios/LintRules`, con SwiftSyntax (el parser oficial de Swift) y sus
  propios tests, igual que `detekt-rules` en Android. SwiftLint queda para el estilo
  general.
- **CI.** El repositorio es privado y GitHub cuenta cada minuto de macOS como diez. El
  usuario eligió que `checks` y `tests` corran solo a mano (`workflow_dispatch`); en
  local, el Stop hook corre lo mismo.
- **iOS mínimo 17.0**, por `@Observable`. Bundle id igual al package de Android.

## Instalación y configuración

- `brew install xcodegen swiftlint` (XcodeGen 2.46.0, SwiftLint 0.65.1). Xcode 27.2 con
  Swift 6.4; simulador fijo para tests: iPhone 17 con iOS 27.2.
- Dependencias por SPM: Apollo iOS 2.5.0, swift-snapshot-testing 1.19.7, swift-syntax
  604.0.0 (para `LintRules`).
- CLI de codegen de Apollo, una vez, desde `ios/Packages/`:
  `swift package --allow-writing-to-package-directory --allow-network-connections all apollo-cli-install`
  (deja `apollo-ios-cli`, ignorado por git). Genera en `Packages/API/Generated/` con
  `./apollo-ios-cli generate`.
- `ios/Config/Local.xcconfig` (no se sube), copiado de `Local.example.xcconfig`:
  `BACKEND_URL` y `APP_STORE_URL`. En los xcconfig `//` empieza un comentario, así que la
  URL se escribe `https:/$()/<dominio>/graphql`.
- Ícono: el de 1024 px de la app anterior, aplanado sobre blanco (la App Store no acepta
  transparencia), como ícono único de Xcode.

## Problemas y soluciones

- **"Fulbito" en un identificador**: el chequeo de idioma lo traduce a "group". El
  proyecto, el target y el esquema se llaman `App` y la entrada `MainApp`; "fulbito"
  queda solo en el bundle id, que es la identidad de la tienda.
- **El target de UI tests no firmaba** sin `Info.plist`: `GENERATE_INFOPLIST_FILE: YES`.
- **Targets vacíos**: SPM y Xcode necesitan al menos un archivo por target; el andamiaje
  deja uno por capa, que reemplaza la implementación del 0006.

## Otras notas

- El usuario abrió el proyecto en Xcode, corrió la app (pantalla en blanco, ícono
  "MatchFulbito", cambia con el modo oscuro) y dio el andamiaje por terminado el
  2026-11-16.

## Implementación del 0006 (TDD)

- **Tokens de SwiftUI.** `sync_contracts.py` genera `Packages/UI/Theme/Generated/Tokens.swift`:
  un `struct Tokens` con una propiedad tipada por token (`Color`, `CGFloat`,
  `Font.Weight`, `String`) en camelCase y las instancias `Tokens.white` y `Tokens.dark`.
  Los colores usan un inicializador privado `Color(argb:)` del mismo archivo; los pesos
  numéricos se traducen a los de SwiftUI (600 → `.semibold`). El schema se copia a
  `ios/graphql/schema.graphql`.
- **Tema.** `AppTheme { ... }` lee el modo claro u oscuro del sistema y pone los tokens en
  el entorno (`@Environment(\.tokens)`); registra Inter (el mismo `.ttf` variable de
  Android) una sola vez desde el paquete.
- **Apollo iOS 2.** Un `InterceptorProvider` propio agrega dos interceptores: uno HTTP
  que pone `X-Client-Platform: ios` y `X-Client-Version` (el número de build), y uno de
  GraphQL que enciende `VersionGate` cuando un error trae `UPGRADE_REQUIRED`. Los tipos
  generados viven en el namespace `GraphQLSchema` dentro del target `API`: Apollo no
  acepta `Schema` (choca con un tipo generado) ni `API` (el nombre del módulo), y con
  `moduleType: other` no genera el namespace, así que se usa `embeddedInTarget`.
- **Prueba de interfaz.** El usuario eligió lanzar la app con `BACKEND_STUB=healthy` en
  los tests de interfaz (la app usa una respuesta fija de `health`), en vez de depender
  del backend real por el túnel.
- **`UI.Button`.** Mantiene el nombre de Android y web; choca con `SwiftUI.Button`, así
  que dentro de `UI` el botón del sistema se escribe `SwiftUI.Button`.
- **Reuse guard.** Pidió revisar antes de crear cada componente de `UI`; ninguno existía
  en iOS y todos llevan el nombre que tienen en los otros clientes.
- **Capturas.** Swift Testing agrega el nombre de la función a las referencias
  (`snapshots-dark.home-white.png`). La primera corrida las graba y falla; la segunda
  compara.
- **Verificado a mano por Claude**: la app en el simulador contra el backend real por
  ngrok muestra Inicio, en claro y en oscuro (`xcrun simctl ui booted appearance dark`).
- El usuario probó la app en Xcode ("tiene lo mismo que android y cambia el estilo") y
  dio el 0006 por terminado el 2026-11-16.
