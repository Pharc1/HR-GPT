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
let pointCloud; // Déclare la variable pour le pointCloud ici

loader.load(
    'static/model.stl',
    (geometry) => {
        const vertices = geometry.attributes.position.array;
        const particleGeometry = new THREE.BufferGeometry();

        const scale = 0.1;
        const pointCount = vertices.length / 3;
        const positions = new Float32Array(pointCount * 3);

        let centerX = 0, centerY = 0, centerZ = 0;

        for (let i = 0; i < pointCount; i++) {
            centerX += vertices[i * 3];
            centerY += vertices[i * 3 + 1];
            centerZ += vertices[i * 3 + 2];
            positions[i * 3] = vertices[i * 3] * scale;
            positions[i * 3 + 1] = vertices[i * 3 + 1] * scale;
            positions[i * 3 + 2] = vertices[i * 3 + 2] * scale;
        }

        centerX /= pointCount * scale;
        centerY /= pointCount * scale;
        centerZ /= pointCount * scale;

        particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const material = new THREE.PointsMaterial({ color: 0x9b59b6, size: 0.00001 });
        pointCloud = new THREE.Points(particleGeometry, material); // Assigne le pointCloud
        scene.add(pointCloud);

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

            pointCloud.rotation.y += 0.0001;

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

document.querySelectorAll('.clickable').forEach(item => {
    item.addEventListener('click', function() {
        // Remplir le champ input avec le texte de l'élément cliqué
        document.getElementById('question').value = this.textContent;
        

        document.querySelector('.send-button').click();
    });
});


const responseTextElement = document.getElementById('responseText');
const questionInput = document.getElementById('question');

document.getElementById("questionForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    responseTextElement.innerHTML = ''; // Clear previous response

    const answerSection = document.getElementById("answerSection");
    answerSection.style.display = 'block'; // Assure que la réponse est visible

    gsap.fromTo(answerSection, {
        opacity: 0,
        y: 20
    }, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        ease: "power2.inOut"
    });

    const decoder = new TextDecoder("utf-8");
    let output = "";

    // Commencer à pulser en rouge
    pulseColor(0xff0000);

    try {
        const response = await fetch(`/ask?question=${encodeURIComponent(questionInput.value)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: questionInput.value }),
            cache: "no-cache" // Ensure no caching issues
        });

        if (!response.ok) {
            throw new Error("Erreur de réseau : " + response.statusText);
        }

        const reader = response.body.getReader();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            output += decoder.decode(value);
            responseTextElement.innerHTML = marked.parse(output);
            console.log('Contenu mis à jour :', responseTextElement.innerHTML);
        }

    } catch (error) {
        console.error("Erreur lors de la requête : ", error);
        responseTextElement.innerHTML = "Erreur lors du traitement de la requête.";
    } finally {
        // Arrêter de pulser et revenir à la couleur d'origine
        stopPulsing();
    }

    // Animer les éléments à cacher
    gsap.to(".meet-gpt-text", {
        opacity: 0,
        height: 0,
        duration: 0.5,
        ease: "power2.inOut",
        onComplete: function () {
            document.querySelector('.meet-gpt-text').style.display = 'none';
        }
    });

    gsap.to(".suggestions-title", {
        opacity: 0,
        height: 0,
        duration: 0.5,
        ease: "power2.inOut",
        onComplete: function () {
            document.querySelector('.suggestions-title').style.display = 'none';
        }
    });

    gsap.to(".example-questions", {
        opacity: 0,
        height: 0,
        duration: 0.5,
        ease: "power2.inOut",
        onComplete: function () {
            document.querySelector('.example-questions').style.display = 'none';
        }
    });

    gsap.to("#questionForm", {
        y: -100,
        scaleX: 1.05,
        scaleY: 1.05,
        duration: 0.4,
        ease: "power2.inOut"
    });
});

// Fonction pour pulser la couleur
function pulseColor() {
    gsap.to(pointCloud.material.color, {
        r: 0.84, // Lavande
        g: 0.78,
        b: 0.88,
        duration: 0.9,
        repeat: -1,
        yoyo: true,
        ease: "power1.inOut"
    });
}

// Fonction pour arrêter de pulser
function stopPulsing() {
    gsap.killTweensOf(pointCloud.material.color); // Arrête toutes les animations sur la couleur
    pointCloud.material.color.set(0x9b59b6); // Remet la couleur d'origine
}
