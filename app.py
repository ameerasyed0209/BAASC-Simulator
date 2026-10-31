import streamlit as st
import streamlit.components.v1 as components
import math

st.set_page_config(
    page_title="BAASC | H₂S Wristband Simulator",
    page_icon="⌚",
    layout="wide",
)

st.markdown("""
<style>
:root { color-scheme:light; }
.block-container {
    max-width: 1500px;
    padding-top: 1.4rem;
}
[data-testid="stAppViewContainer"] {
    background:#f5f8fc !important;
    color:#26394d !important;
}
[data-testid="stHeader"] { background:#f5f8fc !important; }
.stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3 {
    color:#173d79 !important;
}
.stApp [data-testid="stMarkdownContainer"] p,
.stApp label { color:#40536a; }
.subtitle { color: #63738a; margin-bottom: 20px; }
/* H2S slider only: elements are tagged by the helper script at the end of this file */
[data-h2s-hide="1"] { visibility: hidden !important; }
[data-h2s-end="min"], [data-h2s-end="max"] {
    font-size: 0 !important;
    overflow: visible !important;
}
[data-h2s-end="min"]::after, [data-h2s-end="max"]::after {
    font-size: 0.875rem;
    white-space: nowrap;
}
[data-h2s-end="min"]::after { content: "LOW"; }
[data-h2s-end="max"]::after { content: "HIGH"; }
.warning {
    background: #fff4df;
    color: #754b13;
    border: 1px solid #e8c98e;
    border-left: 5px solid #c47b16;
    border-radius: 10px;
    padding: 15px 16px;
    line-height: 1.55;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    "<small>BAASC · BREATHE AWARENESS AND SAFETY CARE · SIH 2026</small>",
    unsafe_allow_html=True,
)
st.title("H₂S Exposure-Dosimeter Wristband")
st.markdown(
    '<p class="subtitle">Interactive virtual prototype · '
    'Adjust exposure conditions and rotate the wristband.</p>',
    unsafe_allow_html=True,
)


def blend(color_a, color_b, amount):
    amount = max(0, min(1, amount))
    return [
        round(color_a[i] + (color_b[i] - color_a[i]) * amount)
        for i in range(3)
    ]


def simulated_colour(concentration, duration):
    # Illustrative visual formula only; not calibrated chemistry.
    response = 1 - math.exp(-(concentration * duration) / 120)

    purple = [118, 32, 92]
    orange = [232, 138, 50]
    yellow = [229, 200, 42]

    if response <= 0.5:
        rgb = blend(purple, orange, response / 0.5)
    else:
        rgb = blend(orange, yellow, (response - 0.5) / 0.5)

    return "#" + "".join(f"{value:02X}" for value in rgb)


left, right = st.columns([1.2, 0.8], gap="large")

with right:
    st.subheader("Exposure controls")

    concentration = st.slider(
        "H₂S concentration (ppm)",
        min_value=0, max_value=80, value=20, step=1,
        key="h2s_slider",
    )

    temperature = st.slider(
        "Temperature (°C)",
        min_value=15, max_value=40, value=25,
    )

    humidity = st.slider(
        "Relative humidity (%)",
        min_value=30, max_value=60, value=45,
    )

    duration = st.slider(
        "Exposure duration (hours)",
        min_value=0.0, max_value=12.0, value=2.0, step=0.5,
    )

    patch_colour = simulated_colour(concentration, duration)
    previous_patch_colour = st.session_state.get("patch_colour", patch_colour)
    st.session_state["patch_colour"] = patch_colour
    nominal_exposure = concentration * duration

    st.metric("Nominal concentration-duration product", f"{nominal_exposure:g} ppm·h")
    st.caption("Nominal ppm·h = concentration × duration; this is not an absorbed dose or validated risk measurement.")
    st.markdown(f"**Illustrative patch colour:** `{patch_colour}`")
    st.markdown(
        f'<div style="height:34px;border-radius:8px;'
        f'background:{patch_colour};border:1px solid #aab3bf;"></div>',
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown(
        f"""
        <div class="warning">
        <b>SIMULATED — NOT CALIBRATED.</b>
        This is an illustrative software model, not a validated H₂S detector
        or safety device. Actual Cu-PAN patch response requires experimental
        calibration.<br>
        Temperature ({temperature} °C) and relative humidity ({humidity}%)
        are displayed as inputs and do not affect the illustrative colour.
        </div>
        """,
        unsafe_allow_html=True,
    )

with left:
    st.subheader("3D wristband preview")
    st.caption("Drag to rotate · scroll to zoom · tap the patch to enlarge · tap QR/reference target for information")

    # The HTML viewer uses real Three.js geometry and interactive camera controls.
    viewer = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing:border-box; }
html,body {
    margin:0;width:100%;height:100%;overflow:hidden;
    font-family:Arial,sans-serif;
    background:radial-gradient(ellipse at 50% 34%,#ffffff 0%,#f3f6fa 64%,#e9eef5 100%);
}
canvas {position:absolute;inset:0;display:block;width:100%;height:100%;touch-action:none}
.hud {
    position:absolute;top:13px;left:14px;z-index:2;
    padding:8px 11px;border:1px solid #e2e8ef;border-radius:9px;
    background:#ffffffeb;color:#304258;
    font-size:10px;font-weight:bold;letter-spacing:1px;pointer-events:none;
}
.note {
    position:absolute;bottom:12px;right:12px;z-index:2;
    background:#ffffffeb;color:#53647a;padding:7px 9px;
    border:1px solid #e2e8ef;border-radius:8px;font-size:10px;pointer-events:none;
}
.status {
    position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
    padding:24px;color:#526174;text-align:center;font-size:14px;
}
.status.error {color:#853c35}
.info-panel {
    position:absolute;z-index:4;left:50%;top:50%;width:min(360px,calc(100% - 32px));
    transform:translate(-50%,-50%);padding:19px 20px;
    color:#26394d;background:#fffffffa;border:1px solid #dfe6ee;
    border-radius:14px;box-shadow:0 16px 48px #13223830;
}
.info-panel[hidden] {display:none}
.info-panel h2 {margin:0 36px 10px 0;color:#173d79;font-size:18px}
.info-panel p {margin:0;color:#43556a;font-size:14px;line-height:1.55}
.info-close {
    position:absolute;top:10px;right:11px;width:32px;height:32px;
    border:0;border-radius:8px;background:#edf2f7;color:#31465d;
    font-size:20px;cursor:pointer;
}
.zoom-hint {
    position:absolute;z-index:2;left:50%;top:56px;transform:translateX(-50%);
    max-width:calc(100% - 28px);padding:7px 10px;border:1px solid #e2e8ef;
    border-radius:8px;background:#ffffffeb;color:#45596e;
    font-size:10px;text-align:center;white-space:nowrap;pointer-events:none;
}
.viewer {
    position:relative;width:100%;height:560px;min-height:390px;
    overflow:hidden;border:1px solid #e1e7ee;border-radius:18px;
    box-shadow:0 12px 32px #263b5310;
}
@media (max-width:560px) {
    .viewer { height:470px; }
    .note { max-width:190px;text-align:right; }
}
</style>
</head>
<body>
<div class="viewer">
<div class="hud">BAASC · VIRTUAL WEARABLE</div>
<div class="note">ILLUSTRATIVE DIGITAL MODEL · NOT A SAFETY DEVICE</div>
<div class="zoom-hint">Tap patch to enlarge · tap QR or reference target for information</div>
<canvas id="view"></canvas>
<div class="status" id="status">Loading interactive 3D model…</div>
<section class="info-panel" id="info-panel" role="dialog" aria-modal="true" aria-labelledby="info-title" hidden>
    <button class="info-close" id="info-close" type="button" aria-label="Close information">×</button>
    <h2 id="info-title"></h2>
    <p id="info-copy"></p>
</section>

<script type="importmap">
{
    "imports": {
        "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
    }
}
</script>
<script>
const canvas=document.getElementById('view');
const status=document.getElementById('status');
const infoPanel=document.getElementById('info-panel');
const infoTitle=document.getElementById('info-title');
const infoCopy=document.getElementById('info-copy');
const previousPatchColour='__PREVIOUS_PATCH_COLOUR__';
const targetPatchColour='__PATCH_COLOUR__';

function showError(message) {
    status.textContent=message;
    status.classList.add('error');
    status.style.background='linear-gradient(180deg,#f6f8fbdd,#edf1f6dd)';
}

async function createViewer() {
    let renderer;
    try {
        const [THREE,controlsModule]=await Promise.all([
            import('https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js'),
            import('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js')
        ]);
        const {OrbitControls}=controlsModule;
        renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
        renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
        renderer.setSize(canvas.clientWidth,canvas.clientHeight,false);
        renderer.shadowMap.enabled=true;
        renderer.shadowMap.type=THREE.PCFSoftShadowMap;
        renderer.outputColorSpace=THREE.SRGBColorSpace;
        renderer.toneMapping=THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure=1.05;

        const scene=new THREE.Scene();
        const camera=new THREE.PerspectiveCamera(
            32,canvas.clientWidth/canvas.clientHeight,0.1,100
        );
        camera.position.set(5.0,2.1,6.5);

        const controls=new OrbitControls(camera,renderer.domElement);
        controls.enableDamping=true;
        controls.dampingFactor=0.075;
        controls.minDistance=5.1;
        controls.maxDistance=11.5;
        controls.target.set(0,0,0);
        controls.maxPolarAngle=Math.PI*0.83;
        controls.minPolarAngle=Math.PI*0.17;
        controls.addEventListener('start',()=>{cameraTransition=null;});

        scene.add(new THREE.HemisphereLight(0xffffff,0x687589,2.1));
        const key=new THREE.DirectionalLight(0xffffff,3.4);
        key.position.set(4,7,6);
        key.castShadow=true;
        key.shadow.mapSize.set(1024,1024);
        key.shadow.camera.left=-4;
        key.shadow.camera.right=4;
        key.shadow.camera.top=5;
        key.shadow.camera.bottom=-5;
        scene.add(key);
        const fill=new THREE.DirectionalLight(0xd9e7fa,1.8);
        fill.position.set(-5,2,4);
        scene.add(fill);
        const rim=new THREE.DirectionalLight(0xffffff,2.4);
        rim.position.set(1,5,-5);
        scene.add(rim);

        const floor=new THREE.Mesh(
            new THREE.PlaneGeometry(100,100),
            new THREE.MeshStandardMaterial({color:'#f0f3f7',roughness:0.95})
        );
        floor.rotation.x=-Math.PI/2;
        floor.position.y=-2.04;
        floor.receiveShadow=true;
        scene.add(floor);

        const watch=new THREE.Group();
        watch.position.z=-0.42;
        scene.add(watch);

        // A rounded rectangular cross-section gives the closed silicone strap a molded profile.
        const strapMaterial=new THREE.MeshStandardMaterial({
            color:'#d9dce0',roughness:0.72,metalness:0.015
        });
        const segments=220;
        const halfWidth=0.31;
        const halfThickness=0.075;
        const corner=0.055;
        const crossSection=[];
        for(const [cx,cy,start] of [
            [halfWidth-corner,halfThickness-corner,0],
            [-halfWidth+corner,halfThickness-corner,90],
            [-halfWidth+corner,-halfThickness+corner,180],
            [halfWidth-corner,-halfThickness+corner,270]
        ]){
            for(let step=0;step<=5;step++){
                const angle=(start+step*18)*Math.PI/180;
                crossSection.push([
                    cx+corner*Math.cos(angle),
                    cy+corner*Math.sin(angle)
                ]);
            }
        }
        const vertices=[];
        const indices=[];
        for(let i=0;i<=segments;i++){
            const t=(i/segments)*Math.PI*2;
            const y=1.79*Math.cos(t);
            const z=-1.05+0.60*Math.sin(t);
            const tangentY=-1.79*Math.sin(t);
            const tangentZ=0.60*Math.cos(t);
            const tangentLength=Math.hypot(tangentY,tangentZ);
            const normalY=-tangentZ/tangentLength;
            const normalZ=tangentY/tangentLength;
            for(const [xOffset,normalOffset] of crossSection){
                vertices.push(
                    xOffset,
                    y+normalY*normalOffset,
                    z+normalZ*normalOffset
                );
            }
        }
        const sectionSize=crossSection.length;
        for(let i=0;i<segments;i++){
            const a=i*sectionSize;
            const b=a+sectionSize;
            for(let j=0;j<sectionSize;j++){
                const next=(j+1)%sectionSize;
                indices.push(a+j,b+j,a+next,b+j,b+next,a+next);
            }
        }
        const strapGeometry=new THREE.BufferGeometry();
        strapGeometry.setAttribute(
            'position',new THREE.Float32BufferAttribute(vertices,3)
        );
        strapGeometry.setIndex(indices);
        strapGeometry.computeVertexNormals();
        const strap=new THREE.Mesh(strapGeometry,strapMaterial);
        strap.castShadow=true;
        strap.receiveShadow=true;
        watch.add(strap);

        function roundedShape(width,height,radius) {
            const s=new THREE.Shape();
            s.moveTo(-width/2+radius,-height/2);
            s.lineTo(width/2-radius,-height/2);
            s.quadraticCurveTo(width/2,-height/2,width/2,-height/2+radius);
            s.lineTo(width/2,height/2-radius);
            s.quadraticCurveTo(width/2,height/2,width/2-radius,height/2);
            s.lineTo(-width/2+radius,height/2);
            s.quadraticCurveTo(-width/2,height/2,-width/2,height/2-radius);
            s.lineTo(-width/2,-height/2+radius);
            s.quadraticCurveTo(-width/2,-height/2,-width/2+radius,-height/2);
            return s;
        }

        function makePanel(width,height,radius,depth,material,z,bevel=0.025) {
            const geometry=new THREE.ExtrudeGeometry(
                roundedShape(width,height,radius),
                {
                    depth,bevelEnabled:true,bevelSegments:4,
                    bevelSize:bevel,bevelThickness:bevel,curveSegments:16
                }
            );
            const mesh=new THREE.Mesh(geometry,material);
            mesh.position.z=z;
            mesh.castShadow=true;
            mesh.receiveShadow=true;
            watch.add(mesh);
            return mesh;
        }

        const steel=new THREE.MeshStandardMaterial({
            color:'#aab5c2',metalness:0.78,roughness:0.24
        });
        const polishedSteel=new THREE.MeshStandardMaterial({
            color:'#e4e9ef',metalness:0.72,roughness:0.19
        });
        const bezel=new THREE.MeshStandardMaterial({
            color:'#c3c9cf',metalness:0.46,roughness:0.3
        });
        const dial=new THREE.MeshStandardMaterial({
            color:'#f4f6f8',metalness:0.12,roughness:0.34
        });
        const darkMetal=new THREE.MeshStandardMaterial({
            color:'#586574',metalness:0.83,roughness:0.27
        });

        // Layered case, chamfered bezel, and a pale dial keep the inset patch prominent.
        makePanel(1.02,3.02,0.25,0.20,steel,-0.02,0.035);
        makePanel(0.97,2.95,0.23,0.07,polishedSteel,0.17,0.02);
        makePanel(0.92,2.89,0.21,0.035,bezel,0.24,0.012);
        makePanel(0.86,2.83,0.18,0.025,dial,0.29,0.01);

        // A lightly fibred polymer/paper texture makes the sensor layer read as an insert.
        const paperCanvas=document.createElement('canvas');
        paperCanvas.width=256;
        paperCanvas.height=256;
        const paperContext=paperCanvas.getContext('2d');
        const paperPixels=paperContext.createImageData(256,256);
        for(let i=0;i<paperPixels.data.length;i+=4){
            const shade=239+Math.floor(Math.random()*17);
            paperPixels.data[i]=shade;
            paperPixels.data[i+1]=shade;
            paperPixels.data[i+2]=shade;
            paperPixels.data[i+3]=255;
        }
        paperContext.putImageData(paperPixels,0,0);
        const paperTexture=new THREE.CanvasTexture(paperCanvas);
        paperTexture.colorSpace=THREE.SRGBColorSpace;

        const patchFrame=new THREE.MeshStandardMaterial({
            color:'#ad9678',roughness:0.62,metalness:0.08
        });
        const patchMaterial=new THREE.MeshStandardMaterial({
            color:previousPatchColour,map:paperTexture,roughness:0.84,
            metalness:0.0
        });
        const patchFramePanel=makePanel(
            0.68,0.56,0.095,0.035,patchFrame,0.325,0.01
        );
        const patchSurface=makePanel(
            0.60,0.48,0.075,0.026,patchMaterial,0.367,0.007
        );
        patchFramePanel.userData.hotspot='patch';
        patchSurface.userData.hotspot='patch';
        patchMaterial.polygonOffset=true;
        patchMaterial.polygonOffsetFactor=-1;
        patchMaterial.polygonOffsetUnits=-1;
        patchFramePanel.position.y=0.82;
        patchSurface.position.y=0.82;

        const labelCanvas=document.createElement('canvas');
        labelCanvas.width=512;
        labelCanvas.height=128;
        const labelContext=labelCanvas.getContext('2d');
        labelContext.fillStyle='#f4f6f8';
        labelContext.fillRect(0,0,512,128);
        labelContext.fillStyle='#20334c';
        labelContext.textAlign='center';
        labelContext.font='600 38px Arial';
        labelContext.fillText('H₂S  DOSIMETER',256,62);
        labelContext.font='20px Arial';
        labelContext.fillText('ILLUSTRATIVE MODEL',256,98);
        const labelTexture=new THREE.CanvasTexture(labelCanvas);
        labelTexture.colorSpace=THREE.SRGBColorSpace;
        const label=new THREE.Mesh(
            new THREE.PlaneGeometry(0.72,0.18),
            new THREE.MeshBasicMaterial({
                map:labelTexture,transparent:true,depthWrite:false
            })
        );
        label.position.set(0,-0.36,0.334);
        watch.add(label);

        // The QR graphic is illustrative; it does not encode cartridge data.
        const detailCanvas=document.createElement('canvas');
        detailCanvas.width=180;
        detailCanvas.height=180;
        const detailContext=detailCanvas.getContext('2d');
        detailContext.fillStyle='#ffffff';
        detailContext.fillRect(0,0,180,180);
        detailContext.fillStyle='#1d2938';
        const qrCells=[
            '111011101','101010101','111011101','000100010','110111011',
            '010101010','111010111','101000101','111011111'
        ];
        for(let row=0;row<9;row++){
            for(let col=0;col<9;col++){
                if(qrCells[row][col]==='1'){
                    detailContext.fillRect(15+col*16,15+row*16,14,14);
                }
            }
        }
        const detailTexture=new THREE.CanvasTexture(detailCanvas);
        detailTexture.colorSpace=THREE.SRGBColorSpace;
        const qrTile=new THREE.Mesh(
            new THREE.PlaneGeometry(0.34,0.34),
            new THREE.MeshBasicMaterial({map:detailTexture})
        );
        qrTile.userData.hotspot='qr';
        qrTile.position.set(0,0.25,0.33);
        watch.add(qrTile);

        const referenceColors=[
            {name:'WHITE',color:'#ffffff'},
            {name:'GREY',color:'#92979d'},
            {name:'BLUE',color:'#159bd2'},
            {name:'DARK GREY',color:'#33383e'}
        ];
        const referenceSwatches=[];
        for(let index=0;index<referenceColors.length;index++){
            const swatch=new THREE.Mesh(
                new THREE.BoxGeometry(0.14,0.12,0.022),
                new THREE.MeshStandardMaterial({
                    color:referenceColors[index].color,
                    roughness:0.62,
                    metalness:0.0
                })
            );
            swatch.position.set(-0.30+index*0.20,-1.19,0.326);
            swatch.userData.hotspot='reference';
            swatch.castShadow=true;
            watch.add(swatch);
            referenceSwatches.push(swatch);
        }
        const referenceLabelCanvas=document.createElement('canvas');
        referenceLabelCanvas.width=512;
        referenceLabelCanvas.height=64;
        const referenceLabelContext=referenceLabelCanvas.getContext('2d');
        referenceLabelContext.fillStyle='#f4f6f8';
        referenceLabelContext.fillRect(0,0,512,64);
        referenceLabelContext.fillStyle='#26394d';
        referenceLabelContext.textAlign='center';
        referenceLabelContext.textBaseline='middle';
        referenceLabelContext.font='600 25px Arial';
        for(let index=0;index<referenceColors.length;index++){
            referenceLabelContext.fillText(
                referenceColors[index].name,64+index*128,32
            );
        }
        const referenceLabelTexture=new THREE.CanvasTexture(referenceLabelCanvas);
        referenceLabelTexture.colorSpace=THREE.SRGBColorSpace;
        const referenceLabels=new THREE.Mesh(
            new THREE.PlaneGeometry(0.76,0.095),
            new THREE.MeshBasicMaterial({
                map:referenceLabelTexture,transparent:true,depthWrite:false
            })
        );
        referenceLabels.position.set(0,-1.34,0.33);
        watch.add(referenceLabels);

        const referenceHotspot=new THREE.Mesh(
            new THREE.PlaneGeometry(0.78,0.34),
            new THREE.MeshBasicMaterial({
                transparent:true,opacity:0,depthWrite:false,
                side:THREE.DoubleSide
            })
        );
        referenceHotspot.position.set(0,-1.245,0.36);
        referenceHotspot.userData.hotspot='reference';
        watch.add(referenceHotspot);

        const fastenerMaterial=new THREE.MeshStandardMaterial({
            color:'#b6bbc1',metalness:0.62,roughness:0.34
        });
        const sideButton=new THREE.Mesh(
            new THREE.CylinderGeometry(0.075,0.075,0.18,32),fastenerMaterial
        );
        sideButton.rotation.z=Math.PI/2;
        sideButton.position.set(0.52,0.38,0.08);
        sideButton.castShadow=true;
        watch.add(sideButton);
        const sideButtonCap=new THREE.Mesh(
            new THREE.CylinderGeometry(0.048,0.048,0.018,32),bezel
        );
        sideButtonCap.rotation.z=Math.PI/2;
        sideButtonCap.position.set(0.62,0.38,0.08);
        watch.add(sideButtonCap);
        for(const y of [-1.40,1.40]){
            const fastener=new THREE.Mesh(
                new THREE.CylinderGeometry(0.07,0.07,0.025,32),fastenerMaterial
            );
            fastener.rotation.x=Math.PI/2;
            fastener.position.set(0,y,-0.03);
            watch.add(fastener);
        }

        const pinMaterial=new THREE.MeshStandardMaterial({
            color:'#111820',roughness:0.62
        });
        for(const t of [2.7,2.9,3.1,3.3,3.5,3.7]){
            const y=1.79*Math.cos(t);
            const z=-1.05+0.60*Math.sin(t);
            const tangentY=-1.79*Math.sin(t);
            const tangentZ=0.60*Math.cos(t);
            const tangentLength=Math.hypot(tangentY,tangentZ);
            const normalY=-tangentZ/tangentLength;
            const normalZ=tangentY/tangentLength;
            const hole=new THREE.Mesh(
                new THREE.CylinderGeometry(0.043,0.043,0.018,24),pinMaterial
            );
            hole.rotation.x=Math.atan2(normalZ,normalY);
            hole.position.set(0,y+normalY*0.078,z+normalZ*0.078);
            hole.castShadow=true;
            watch.add(hole);
        }
        for(const y of [-1.52,1.52]){
            const pin=new THREE.Mesh(
                new THREE.CylinderGeometry(0.038,0.038,0.54,24),fastenerMaterial
            );
            pin.rotation.z=Math.PI/2;
            pin.position.set(0,y,-0.28);
            pin.castShadow=true;
            watch.add(pin);
        }

        watch.rotation.x=-0.035;
        watch.rotation.y=-0.14;

        const startColour=new THREE.Color(previousPatchColour);
        const endColour=new THREE.Color(targetPatchColour);
        const transitionStarted=performance.now();
        const transitionDuration=460;
        const initialCameraPosition=camera.position.clone();
        const initialTarget=controls.target.clone();
        let zoomedToPatch=false;
        let cameraTransition=null;
        const raycaster=new THREE.Raycaster();
        const pointer=new THREE.Vector2();
        let pointerDown=null;

        function transitionCamera(position,target) {
            cameraTransition={
                start:performance.now(),
                duration:420,
                fromPosition:camera.position.clone(),
                toPosition:position.clone(),
                fromTarget:controls.target.clone(),
                toTarget:target.clone()
            };
        }

        function showInfo(title,copy) {
            infoTitle.textContent=title;
            infoCopy.textContent=copy;
            infoPanel.hidden=false;
        }

        function activateHotspot(hotspot) {
            if(hotspot==='patch'){
                infoPanel.hidden=true;
                if(zoomedToPatch){
                    zoomedToPatch=false;
                    controls.minDistance=5.1;
                    transitionCamera(initialCameraPosition,initialTarget);
                    return;
                }
                watch.updateMatrixWorld(true);
                const patchCenter=patchSurface.localToWorld(
                    new THREE.Vector3(0,0,0.02)
                );
                const viewDirection=camera.position.clone().sub(controls.target).normalize();
                zoomedToPatch=true;
                controls.minDistance=2.2;
                transitionCamera(
                    patchCenter.clone().add(viewDirection.multiplyScalar(2.35)),
                    patchCenter
                );
                return;
            }
            if(hotspot==='qr'){
                showInfo(
                    'Micro QR · cartridge record',
                    'A real cartridge QR code is intended to carry its badge ID, batch number, manufacture date, and expiry date. An app could read those fields and check whether the cartridge is within its stated validity period. The code shown here is only a visual placeholder: it contains no data, is not scannable, and does not validate a cartridge.'
                );
            } else if(hotspot==='reference'){
                showInfo(
                    'Reference colour target',
                    'The white, grey, blue, and dark-grey target is photographed beside the Cu-PAN sensing patch. Its known colours can help an app correct colour differences caused by lighting and smartphone cameras before comparing the sensing patch. These model colours are illustrative only; they are not a calibrated standard or H₂S measurement.'
                );
            }
        }

        canvas.addEventListener('pointerdown',event=>{
            pointerDown={x:event.clientX,y:event.clientY};
        });
        canvas.addEventListener('pointerup',event=>{
            if(!pointerDown)return;
            const moved=Math.hypot(
                event.clientX-pointerDown.x,event.clientY-pointerDown.y
            );
            pointerDown=null;
            if(moved>9)return;
            const rect=canvas.getBoundingClientRect();
            pointer.x=((event.clientX-rect.left)/rect.width)*2-1;
            pointer.y=-((event.clientY-rect.top)/rect.height)*2+1;
            raycaster.setFromCamera(pointer,camera);
            watch.updateMatrixWorld(true);
            const hit=raycaster.intersectObjects(
                [patchSurface,patchFramePanel,qrTile,referenceHotspot,...referenceSwatches],false
            )[0];
            if(hit)activateHotspot(hit.object.userData.hotspot);
        });
        document.getElementById('info-close').addEventListener('click',()=>{
            infoPanel.hidden=true;
        });
        infoPanel.addEventListener('click',event=>{
            if(event.target===infoPanel)infoPanel.hidden=true;
        });
        window.addEventListener('keydown',event=>{
            if(event.key==='Escape')infoPanel.hidden=true;
        });

        function resize() {
            const width=canvas.clientWidth;
            const height=canvas.clientHeight;
            if(!width||!height)return;
            renderer.setSize(width,height,false);
            camera.aspect=width/height;
            camera.updateProjectionMatrix();
        }
        if(typeof ResizeObserver!=='undefined'){
            new ResizeObserver(resize).observe(canvas);
        }
        window.addEventListener('resize',resize);
        resize();
        status.style.display='none';

        function animate(now) {
            requestAnimationFrame(animate);
            const progress=Math.min((now-transitionStarted)/transitionDuration,1);
            const eased=progress*progress*(3-2*progress);
            patchMaterial.color.copy(startColour).lerp(endColour,eased);
            if(cameraTransition){
                const cameraProgress=Math.min(
                    (now-cameraTransition.start)/cameraTransition.duration,1
                );
                const cameraEase=cameraProgress*cameraProgress*(3-2*cameraProgress);
                camera.position.lerpVectors(
                    cameraTransition.fromPosition,cameraTransition.toPosition,cameraEase
                );
                controls.target.lerpVectors(
                    cameraTransition.fromTarget,cameraTransition.toTarget,cameraEase
                );
                if(cameraProgress===1)cameraTransition=null;
            }
            controls.update();
            renderer.render(scene,camera);
        }
        requestAnimationFrame(animate);
    } catch(error) {
        console.error('Unable to initialize the BAASC 3D viewer:',error);
        if(renderer)renderer.dispose();
        showError(
            'The interactive 3D viewer could not start. Check WebGL support, '+
            'browser hardware acceleration, and your network connection.'
        );
    }
}

createViewer();
</script>
</div>
</body>
</html>
"""

    viewer = viewer.replace("__PATCH_COLOUR__", patch_colour)
    viewer = viewer.replace("__PREVIOUS_PATCH_COLOUR__", previous_patch_colour)

    components.html(
        viewer,
        height=550,
        scrolling=False,
    )

st.divider()
st.caption(
    "BAASC · SIH 2026 · Virtual concept only. "
    "This is not a calibrated chemical sensor or safety device."
)

# Helper for the H2S slider display only (tags its thumb value and end labels).
components.html(
    """
<script>
(function () {
  var doc;
  try { doc = window.parent.document; } catch (e) { return; }
  var win = window.parent;

  function findSlider() {
    var all = doc.querySelectorAll('[data-testid="stSlider"]');
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      if (el.closest('.st-key-h2s_slider')) return el;
      var thumb = el.querySelector('[role="slider"]');
      var label = (thumb && thumb.getAttribute('aria-label')) || '';
      var lab = el.querySelector('[data-testid="stWidgetLabel"]');
      var text = label + ' ' + (lab ? lab.textContent : '');
      if (text.indexOf('concentration') !== -1) return el;
    }
    return null;
  }

  function tag() {
    var slider = findSlider();
    if (!slider) return;
    var nodes = slider.querySelectorAll('*');
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.children.length > 0) continue;
      var t = (n.textContent || '').trim();
      if (!t) continue;
      if (n.closest('[data-testid="stWidgetLabel"]')) continue;
      var tid = '';
      var p = n;
      while (p && p !== slider) {
        tid += ' ' + (p.getAttribute('data-testid') || '');
        p = p.parentElement;
      }
      if (/ThumbValue/.test(tid) || n.closest('[role="slider"]')) {
        n.setAttribute('data-h2s-hide', '1');
      } else if (/TickBarMin/.test(tid) || t === '0') {
        n.setAttribute('data-h2s-end', 'min');
      } else if (/TickBarMax/.test(tid) || t === '80') {
        n.setAttribute('data-h2s-end', 'max');
      }
    }
  }

  if (win.__h2sObserver) { try { win.__h2sObserver.disconnect(); } catch (e) {} }
  var pending = false;
  function schedule() {
    if (pending) return;
    pending = true;
    win.requestAnimationFrame(function () { pending = false; tag(); });
  }
  win.__h2sObserver = new win.MutationObserver(schedule);
  win.__h2sObserver.observe(doc.body, { childList: true, subtree: true, characterData: true });
  tag();
})();
</script>
""",
    height=0,
)
