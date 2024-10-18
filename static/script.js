const scene = new THREE.Scene();

const light = new THREE.SpotLight();
light.position.set(20, 20, 20);
scene.add(light);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 10);
camera.position.z = 5;

const renderer = new THREE.WebGLRenderer({ alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;


const loader = new THREE.STLLoader();
loader.load(
    'static/model.stl',
    (geometry) => {
        const vertices = geometry.attributes.position.array;
        const particleGeometry = new THREE.BufferGeometry();

        // Ajustement de l'échelle pour réduire la taille
        const scale = 0.1;
        const pointCount = vertices.length / 3;
        const positions = new Float32Array(pointCount * 2);

        let centerX = 0, centerY = 0, centerZ = 0;

        for (let i = 0; i < pointCount; i++) {
            centerX += vertices[i * 3];
            centerY += vertices[i * 3 + 1];
            centerZ += vertices[i * 3 + 2];
            positions[i * 3] = vertices[i * 3] * scale;
            positions[i * 3 + 1] = vertices[i * 3 + 1] * scale;
            positions[i * 3 + 2] = vertices[i * 3 + 2] * scale;
        }

        // Calculer le centre
        centerX = centerX / pointCount * scale;
        centerY = centerY / pointCount * scale;
        centerZ = centerZ / pointCount * scale;

        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({ color: 0x9b59b6, size: 0.00001 });
        const pointCloud = new THREE.Points(particleGeometry, material);
        scene.add(pointCloud);

        // Effet de vague autour du logo sur les axes X et Y
        function animate() {
            requestAnimationFrame(animate);

            const time = Date.now() * 0.002;
            for (let i = 0; i < pointCount; i++) {
                const dx = positions[i * 3] - centerX;
                const dy = positions[i * 3 + 1] - centerY;
                const dz = positions[i * 3 + 2] - centerZ;
                const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

                const waveEffect = Math.sin(distance * 10 - time) * 0.05;
                
                positions[i * 3] = (vertices[i * 3] * scale) + waveEffect * dx / distance;
                positions[i * 3 + 1] = (vertices[i * 3 + 1] * scale) + waveEffect * dy / distance;
                positions[i * 3 + 2] = (vertices[i * 3 + 2] * scale) + waveEffect * dz / distance;
            }
            particleGeometry.attributes.position.needsUpdate = true;

            pointCloud.rotation.y += 0.0001; // Rotation de la forme

            controls.update();
            renderer.render(scene, camera);
        }

        animate();
    },
    (xhr) => {
        console.log((xhr.loaded / xhr.total) * 100 + '% loaded');
    },
    (error) => {
        console.error(error);
    }
);

window.addEventListener('resize', onWindowResize);

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}


document.getElementById("questionForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const question = document.getElementById("question").value;

    // Appel à l'API pour obtenir la réponse
    fetch('/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        // Afficher la réponse
        document.getElementById("responseText").textContent = data.answer;

        // Cacher "Rencontrer HR GPT" avec GSAP
        gsap.to(".meet-gpt-text", {
            opacity: 0,
            height: 0,
            duration: 0.5, // Durée légèrement réduite
            ease: "power2.inOut", // Ease plus fluide
            onComplete: function() {
                document.querySelector('.meet-gpt-text').style.display = 'none';
            }
        });

        // Cacher la section "Essayez ça" avec GSAP
        gsap.to(".suggestions-title, .example-questions", {
            opacity: 0,
            height: 0,
            duration: 0.5, // Durée légèrement réduite
            ease: "power2.inOut", // Ease plus fluide
            onComplete: function() {
                document.querySelector('.suggestions-title').style.display = 'none';
                document.querySelector('.example-questions').style.display = 'none';
            }
        });

        // Animer l'input et le bouton pour qu'ils montent en haut
        gsap.to("#questionForm", {
            y: -100,
            scaleX: 1.05, // Scale légèrement réduit pour un effet plus subtil
            scaleY: 1.05,
            duration: 0.4, // Durée légèrement réduite
            ease: "power2.inOut" // Ease plus fluide
        });

        // Afficher la réponse avec une animation de fondu
        const answerSection = document.getElementById("answerSection");
        answerSection.style.display = 'block'; // Assure que la réponse est visible

        // Animation de fondu plus fluide
        gsap.fromTo(answerSection, {
            opacity: 0,
            y: 20 // Déplacement initial plus léger
        }, {
            opacity: 1,
            y: 0,
            duration: 0.5, // Durée légèrement réduite
            ease: "power2.inOut" // Ease plus fluide
        });
    })
    .catch(error => console.error('Erreur:', error));
});
