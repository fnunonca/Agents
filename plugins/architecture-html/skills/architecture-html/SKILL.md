---
name: architecture-html
description: Genera o actualiza docs/architecture.html — una documentación técnica autocontenida con diagrama interactivo React Flow — analizando el código del repo. Úsalo cuando el usuario pida "documentar la arquitectura", "generar architecture.html", "diagrama de capas", "diagrama de interacciones", "onboarding doc", o invoque /architecture-html.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# Architecture HTML Skill

Genera una página HTML estática y autocontenida (sin build) que documenta la arquitectura del repo actual y embebe un diagrama interactivo de React Flow para onboarding.

## Cuándo usarlo

- El usuario pide documentar la arquitectura del proyecto.
- Pide un diagrama de capas / interacciones con BD / servicios externos.
- Pide actualizar `docs/architecture.html` tras cambios estructurales.
- Invoca `/architecture-html`.

## Salida

Un único archivo: `docs/architecture.html`, autocontenido (carga React + React Flow desde `esm.sh` con import map, sin bundler ni npm).

## Pasos

### 1. Reconocer el stack y las capas

Antes de escribir nada, lee:

- `CLAUDE.md` en la raíz (si existe) — es la fuente más fiable.
- Archivos de configuración: `*.csproj`, `*.sln`, `package.json`, `go.mod`, `pyproject.toml`, `pom.xml`.
- Punto de entrada: `Program.cs`, `Startup.cs`, `main.go`, `index.ts`, `app.py`.
- `appsettings*.json` o equivalente para descubrir URLs de servicios externos.

Identifica:

- **Capas / proyectos** de la solución y su dependencia (WebApi → Application → Domain → Infra).
- **Endpoints expuestos** (controladores, handlers, rutas).
- **Servicios externos** consumidos por HTTP (busca `IHttpClientFactory`, `HttpClient`, `IRestClient`, `fetch`, `axios`, URLs en config).
- **Acceso a BD** (repositorios, SPs, ORM). Busca `Dapper`, `DbContext`, `Repository`, `usp_`, `SP_`. **Anota siempre el esquema** (`Tokenization.usp_x`, `DBO.SP_y`) — si conviven varios, sepáralos en nodos distintos en el diagrama, no los unifiques bajo un solo "BD".
- **Trabajo en background** (`Thread`, `Task.Run`, `BackgroundService`, `IHostedService`, jobs).
- **Códigos / convenciones de respuesta** (`ResponseApp<T>`, códigos `00`, `A1`, etc.).
- **Validaciones**, **headers obligatorios**, **secretos** (env vars, encriptación AES/RSA).

Si algo no es derivable del código, no inventes — anótalo como pendiente en la respuesta.

### 2. Estructura del HTML

El archivo final debe tener estas secciones (numéralas y enlázalas desde un **sidebar fijo** a la izquierda — ver punto al final):

1. **Resumen del servicio** — tabla con framework, ORM, BD, logging, URL dev.
2. **Arquitectura y capas**
   - 2.1 Capas de la solución (diagrama vertical CSS).
   - 2.2 Mapa de interacciones (diagrama React Flow interactivo).
   - 2.3 Resumen para onboarding (4 tarjetas: quién habla con qué, BD, externos, background work).
3. **Endpoints expuestos** — uno por bloque, con headers, body, response, códigos.
4. **Flujo interno completo**:
   - 4.1 **Diagrama de secuencia UML** usando **Mermaid** (`https://esm.sh/mermaid@10.9.1`, sin bundler). NO usar React Flow para sequence diagrams — el layout no funciona y los labels se superponen. Mermaid renderiza SVG nativo con `sequenceDiagram`, `participant`, `->>`, `-->>`, `alt/else`, `opt`, `Note over`, `activate/deactivate` — sintaxis estándar UML. Temar con `theme: 'base'` + `themeVariables` alineados con la paleta del documento. Toolbar `Zoom −` / `Zoom +` / `Reset` / `Exportar PNG` / `Pantalla completa` (independiente del helper de React Flow). **Zoom + pan obligatorio** — ver punto 4.1 más abajo. El export serializa el SVG, lo dibuja en un `<canvas>` con `pixelRatio: 2` y fondo `#0f1419`, y descarga vía `canvas.toDataURL('image/png')`; **debe leer el tamaño natural del SVG desde su `viewBox` (no `getBoundingClientRect()`) para no verse afectado por el zoom CSS aplicado al viewport**.
   - 4.2 Detalle paso a paso por capa.
   - 4.3 Bifurcación de la lógica.
   - 4.4 Retorno al cliente.
5. **Servicios externos consumidos** — tabla con cliente HTTP, cuándo se invoca.
6. **Base de datos y objetos** — conexión, SPs/tablas, mapa de uso por paso.
7. **Validaciones del request** — tablas por bloque.

Conserva el orden y la profundidad de detalle del template (`references/template.html`).

**Sidebar de navegación obligatorio**: layout principal en CSS Grid (`grid-template-columns: 260px 1fr`) con `<aside class="sidebar">` `position: sticky; top: 0; max-height: 100vh; overflow-y: auto` a la izquierda y `.main` a la derecha. El sidebar debe:

- Listar las 7 secciones principales con sus IDs (`#overview`, `#architecture`, …).
- Tener un grupo `<ul class="sub-toc">` anidado bajo cada sección que tiene subsecciones relevantes (2.x, 3.x).
- Incluir un script de **scrollspy** con `IntersectionObserver` (`rootMargin: '-10% 0px -75% 0px'`) que aplica la clase `active` al link de la sección visible — sin librerías.
- Colapsarse a barra horizontal en `@media (max-width: 1024px)`.
- `html { scroll-padding-top: 24px }` para que el anchor scrolling no quede pegado arriba.

Todas las subsecciones que aparecen en el sidebar deben tener `id` en su `<h3>`. Las secciones principales (`<h2>`) ya tienen id (`overview`, `architecture`, `endpoints`, `flow`, `externals`, `database`, `validations`) — respétalos como contrato.

### 3. Paleta y estilo

Usa exactamente esta paleta dark (tomada del template):

```
--bg: #0f1419       --panel: #1a1f29      --panel-2: #232a37    --border: #2d3648
--text: #e3e8f0     --muted: #8b95a8      --accent: #7aa2f7     --green: #9ece6a
--orange: #ff9e64   --red: #f7768e        --yellow: #e0af68     --purple: #bb9af7
--cyan: #7dcfff
```

Asignación semántica para los nodos del diagrama:

| Tipo de nodo  | Color   | Cuándo                                      |
|---------------|---------|---------------------------------------------|
| client        | cyan    | Cliente HTTP externo                        |
| controller    | accent  | Capa WebApi / controladores                 |
| application   | green   | Casos de uso / orquestación                 |
| domain        | purple  | Servicios de dominio (donde vive el I/O)    |
| repository    | orange  | Acceso a datos                              |
| database      | yellow  | Motor de BD (SQL Server, Postgres, etc.)    |
| external      | red     | APIs externas consumidas                    |

### 4. Diagrama React Flow — convenciones obligatorias

Carga la librería desde CDN, sin bundler:

```html
<link rel="stylesheet" href="https://esm.sh/@xyflow/react@12/dist/style.css">
<script type="importmap">
{
  "imports": {
    "react": "https://esm.sh/react@18.3.1",
    "react/jsx-runtime": "https://esm.sh/react@18.3.1/jsx-runtime",
    "react-dom": "https://esm.sh/react-dom@18.3.1",
    "react-dom/client": "https://esm.sh/react-dom@18.3.1/client",
    "@xyflow/react": "https://esm.sh/@xyflow/react@12?deps=react@18.3.1,react-dom@18.3.1"
  }
}
</script>
```

**Requisitos del componente:**

- Custom node `LayerNode` con `Handle` en las 4 caras (target arriba+izquierda, source abajo+derecha) e `isConnectable: false`. Si dos nodos necesitan dos edges entre ellos (request/response), añadir handles extra desfasados al 70% de altura (`source-Left` con id `'l-out'` + `target-Right` con id `'r-in'` y `style: { top: '70%' }`) para que las dos edges sigan rutas distintas y sus labels no se apilen.
- Cada nodo renderiza `data.title` (negrita, color por tipo) + lista `data.subs` (mono, muted).
- Usa `useNodesState` + `useEdgesState` con `onNodesChange`/`onEdgesChange` **siempre** — sin esto los nodos no se pueden arrastrar.
- Edges `type: 'smoothstep'` + `MarkerType.ArrowClosed`.
- **Labels de edges**: definir un `lblStyle` / `lblBgStyle` / `lblBgPadding` reutilizable y pasarlo a TODA edge con label. Sin esto los labels son ilegibles. Ejemplo: `labelStyle: { fill: '#e3e8f0', fontSize: 11, fontFamily: 'JetBrains Mono', fontWeight: 500 }`, `labelBgStyle: { fill: '#232a37', stroke: '#2d3648', strokeWidth: 1 }`, `labelBgPadding: [6, 3]`, `labelBgBorderRadius: 4`. Mantener los labels cortos (≤30 chars) — si dos nodos están en filas paralelas (varios Repository → varias BD), sus midpoints caen en la misma franja Y y los labels largos se apilan. En ese caso: acortar labels (sacar info redundante que ya viene del nodo destino) y/o **desfasar los Y** de los nodos de las dos filas (no todos al mismo Y).
- Llamadas síncronas: línea sólida del color del destino.
- Llamadas dentro de Thread/job fire-and-forget: `strokeDasharray: '6 4'` + naranja + `animated: true`.
- Llamadas HTTP a externos: `animated: true`.
- Respuesta al cliente: dashed verde.
- Props del `ReactFlow`: `nodesDraggable: true, nodesConnectable: false, elementsSelectable: true, edgesFocusable: false, fitView: true, fitViewOptions: { padding: 0.2 }, proOptions: { hideAttribution: true }, minZoom: 0.3, maxZoom: 1.5`.
- Children: `<Background variant="dots" gap={24} size={1} color="#2d3648" />`, `<Controls showInteractive={false} />`, `<MiniMap>` con `nodeColor` por `data.kind`, `<Panel position="top-left">` con texto guía.
- **Botón de Pantalla completa**: el contenedor del diagrama debe tener `position: relative` y un botón absoluto en la esquina superior derecha que dispare `requestFullscreen()` / `exitFullscreen()` sobre el wrapper. Incluir reglas CSS `:fullscreen` y `:-webkit-full-screen` para que React Flow ocupe el viewport y se oculte el padding del recuadro. El handler debe alternar el texto del botón ("Pantalla completa" ↔ "Salir pantalla completa") escuchando `fullscreenchange` y `webkitfullscreenchange`.
- **Toolbar reusable** (fullscreen + export PNG): el handler vive en `window.setupRfToolbar({ wrapper, canvas, fileBaseName, fsBtn, fsLabel, exportBtn, exportLabel })`, definido **una vez** en el `<script>` del primer diagrama. Los diagramas siguientes solo llaman a la función pasando sus referencias. Cada wrapper usa la clase `.rf-wrapper` (genérica) y cada canvas la clase `.rf-canvas` (en lugar de `#reactflow-root`, que es específico del mapa de interacciones por compatibilidad).
- **Botón de Exportar PNG**: junto al de pantalla completa, agrupados en una `.rf-toolbar` absoluta arriba-derecha. Usar `html-to-image` (`https://esm.sh/html-to-image@1.11.13`) en el import map. El handler:
  - Calcula bounds **leyendo el DOM** (no `getNodesBounds(initialNodes)` — devuelve mal el ancho porque `initialNodes` no incluye width/height, los pone el CSS): itera `viewport.querySelectorAll('.react-flow__node')`, lee `style.left/top` + el `translate(...)` del `transform` + `offsetWidth/offsetHeight`, y arma `{ x, y, width, height }`. Padding ~60.
  - **Modifica directamente** `viewport.style.transform = translate(padding - bounds.x, padding - bounds.y) scale(1)` (NO usar `getViewportForBounds` + pasar el transform como style a `toPng`: el doble transform corrompe la salida).
  - Espera 2 `requestAnimationFrame` para que el layout se aplique.
  - Llama `toPng(viewport, { backgroundColor, width: imgWidth, height: imgHeight, pixelRatio: 2, filter, style: { width, height, transformOrigin: 'top left' } })`.
  - `filter` excluye `react-flow__minimap`, `react-flow__controls`, `react-flow__panel`, `react-flow__background`, `react-flow__attribution`, `rf-toolbar`.
  - Aplica clase `is-exporting` al wrapper para ocultar handles via CSS (`.is-exporting .react-flow__handle { opacity: 0 }`) — si no, salen como cuadritos negros sucios en la imagen.
  - Restaura el transform original en `finally`.
  - Genera `<a download="architecture-diagram-{ISO-timestamp}.png">` y lo dispara.
  - **Los CSS de `.react-flow__edge-text` y `.react-flow__edge-textbg` deben usar hex absolutos (no `var(--text)` etc.) con `!important`** — `html-to-image` serializa los `<text>` SVG vía `XMLSerializer` y NO incluye CSS custom properties heredadas, así que con `var()` el texto sale invisible y solo se ve el rectángulo de fondo.
  - Como cinturón + tirantes, el handler también debe iterar `.react-flow__edge-text` y `.react-flow__edge-textbg` antes de `toPng` y aplicar `setAttribute('fill', '#hex')` + `style.fill = '#hex'` inline (porque algunos navegadores ignoran `style` en SVG y solo respetan el atributo, otros al revés).

**Layout sugerido** (ajusta a la cantidad de capas/servicios del repo):

- Columnas en `x`: cliente `40`, capa principal `360–660`, repositorios bajo dominios, externos a la derecha `~1100`, BD abajo a la derecha.
- Filas en `y`: ~180 px de separación vertical entre capas.
- Altura del contenedor `#reactflow-root`: ~900 px.
- Nodos: `min-width: 210px`, `max-width: 260px`, `padding: 12px 16px`.

### 4.1. Zoom + pan del diagrama Mermaid (obligatorio)

Mermaid emite el `<svg>` con `width="100%"` aún con `useMaxWidth: false`. Si dejas el SVG así dentro de un wrapper escalado por CSS (`transform: scale()`), el ancho del SVG se renegocia con el viewport en cada reflow y el diagrama se ve borroso/distorsionado al hacer zoom. Por eso este skill **fija el SVG a su tamaño natural en píxeles** antes de aplicar cualquier transform.

Estructura:

- `<pre class="mermaid">` envuelto en `<div class="seq-viewport" id="seq-viewport">` dentro de `.seq-canvas`. El `.seq-canvas` es `position: relative; overflow: hidden; height: 720px; cursor: grab` (y `.is-panning { cursor: grabbing }`). El `.seq-viewport` es `position: absolute; top: 0; left: 0; width: max-content; transform-origin: 0 0`. La regla `.seq-viewport svg { display: block; max-width: none !important }` neutraliza cualquier `max-width` heredado.
- Toolbar (en este orden): `Zoom −`, `Zoom +`, `Reset`, `Exportar PNG`, `Pantalla completa`. IDs: `seq-zoom-out-btn`, `seq-zoom-in-btn`, `seq-zoom-reset-btn`, `seq-export-btn`, `seq-fullscreen-btn`. Reusa la clase `.rf-fullscreen-btn`.
- Indicador `<div class="seq-zoom-indicator" id="seq-zoom-indicator">100%</div>` abajo-izquierda del canvas (`pointer-events: none`). Se actualiza en cada `applyTransform()`.

Estado y helpers (no varíes los nombres — el template los referencia):

- `let zoom = 1; let panX = 0; let panY = 0;` + `let svgNaturalW = 0; let svgNaturalH = 0;`. Límites `ZOOM_MIN = 0.2`, `ZOOM_MAX = 3`, paso `ZOOM_STEP = 1.2`.
- `applyTransform()` → `seqViewport.style.transform = translate(${panX}px, ${panY}px) scale(${zoom})` + actualiza indicador.
- `zoomAt(factor, clientX, clientY)` → zoom hacia el cursor: `ratio = next/zoom; panX = cx - (cx - panX) * ratio` (idem `panY`). Sin coords, usa el centro del canvas.
- `resetZoom()` → **NO uses fit-to-view a ambos ejes**. Los sequence diagrams son muy altos (un flujo de 30 mensajes mide 2000+ px) y un fit completo deja el texto ilegible. Estrategia: `zoom = clamp(max(0.45, min(1, (canvasW-48)/svgNaturalW)), 0.2, 3)`. Es decir, máximo 100%, baja hasta caber en ancho, pero nunca por debajo del 45% (umbral mínimo legible para diagramas con muchos actores). Centrar horizontalmente; `panY = 12` (margen superior chico). El usuario hace pan vertical para recorrer el flujo.
- Llamar `requestAnimationFrame(resetZoom)` después de `mermaid.render(...)` y en `fullscreenchange` / `webkitfullscreenchange`.

**Lo crítico — neutralizar el `width="100%"` de Mermaid**: justo después de `mermaidEl.outerHTML = ...`, lee el SVG resultante y:

1. Parsea `viewBox="x y W H"` (`split(/\s+/).map(Number)`); guarda `svgNaturalW = W`, `svgNaturalH = H`. Fallback si no hay viewBox: `getBoundingClientRect()` (con `scale(1)` temporal).
2. `svgEl.removeAttribute('width'); svgEl.removeAttribute('height');`
3. `svgEl.style.width = svgNaturalW + 'px'; svgEl.style.height = svgNaturalH + 'px'; svgEl.style.maxWidth = 'none';`

Sin estos 3 pasos, el SVG se reflowa con cada `scale()` aplicado al padre y se ve distorsionado / mal medido.

Interacciones:

- Botones `+`, `−`, `Reset`.
- Rueda del mouse sobre `.seq-canvas` con `preventDefault()` (passive: false). Acercar = `deltaY < 0`.
- **Drag-to-pan**: `mousedown` sobre el canvas guarda `dragStart = { x, y, panX, panY }`; `mousemove` en `window` actualiza el pan; `mouseup` en `window` libera. Agrega `.is-panning` al canvas durante el drag para cambiar el cursor.

**Export PNG**: lee `svgNaturalW`/`H` (o el `viewBox` directo del SVG) — NUNCA `getBoundingClientRect()` directo, porque el `transform: scale()` del viewport propagaría a la medición y el PNG saldría al tamaño del zoom actual.

**Naming de `participant` (importante para legibilidad)**:

- Mantén los labels de los `participant ... as ...` **cortos en una sola línea** (≤18 chars). No uses `<br/>` ni nombres tipo `Controller<br/>(TokenizeCybersourceController)`: la versión expandida hace que el SVG natural supere 3500-4000px de ancho y el zoom-fit cae a ~30% (ilegible). La versión corta (`Controller`, `Application`, `CardDomain`, `CybersourceToken`, `SQL Server`, `TokenProvision Biz`, `TokenizeOperation`) deja el SVG en ~3500px y el zoom-fit en ~45-60%.
- En la config de Mermaid `sequence: { ... }`, NO fijes `width`/`height` de los actores. Si los fijas, los nombres más largos que el ancho desaparecen (Mermaid trunca silenciosamente). Deja que Mermaid mida cada actor por su label.
- `actorMargin: 50` y `messageMargin: 40` dan separación cómoda sin inflar el ancho innecesariamente.

### 5. Procedimiento de generación

1. Si `docs/architecture.html` ya existe, léelo primero para preservar decisiones previas (paleta personalizada, secciones añadidas a mano).
2. Si existe `references/template.html` junto a este `SKILL.md`, úsalo como base. Si no, genera el HTML desde cero siguiendo las secciones definidas arriba (este `SKILL.md` es autosuficiente sin template).
3. Reemplaza/actualiza solo lo que cambió: nodos, edges, tablas de SPs/endpoints/servicios. No reescribas el archivo entero a ciegas si ya hay contenido válido.
4. Valida que el HTML quede balanceado (puedes correr un `grep -c` rápido por `<div>`/`</div>`, o un parser XML sobre el bloque SVG si quedara alguno).
5. Avisa al usuario qué encontraste en el escaneo y qué decisiones tomaste (p.ej. "detecté 3 servicios externos y 4 SPs, asumí que `Foo` es fire-and-forget porque vive en `new Thread(...)`").

### 6. Qué NO hacer

- No uses build tools, npm, Vite ni Tailwind — debe abrirse con doble click.
- No inventes endpoints o SPs que no estén en el código.
- No omitas el esquema de los SPs (`schema.SP`) — en el diagrama, en las tablas y en los labels de las flechas. Si el repo tiene más de un schema (`Tokenization`, `DBO`, etc.), usa **un nodo por schema** y agrúpalos visualmente bajo "BD".
- No expliques en código (comentarios) lo que ya está en el HTML renderizado.
- No omitas `useNodesState`/`onNodesChange` — sin eso el diagrama parece roto.
- No uses emojis salvo que el repo ya los use o el usuario los pida.
- No incluyas atribución de React Flow (`proOptions.hideAttribution: true`).

## Archivos de referencia

- `references/template.html` *(opcional)* — versión actual del HTML para usar como modelo de estructura, CSS y código React Flow. El plugin no lo incluye por defecto; colócalo aquí si quieres anclar el output a un template concreto.

## Mejora continua

Este skill vive en el repo. Cuando aprendas algo nuevo sobre cómo el equipo quiere documentar (otra paleta, otra sección, otra convención), edita este `SKILL.md` o el `template.html` y commitéalo.
