const API_URL = "http://localhost:8000";

function crearReserva() {
    const reserva = {
        usuari_id: document.getElementById("usuari").value,
        servei: document.getElementById("servei").value,
        data: document.getElementById("data").value,
        hora_inici: document.getElementById("hora_inici").value,
        hora_fi: document.getElementById("hora_fi").value
    };

    fetch(`${API_URL}/reserves`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reserva)
    })
    .then(async res => {
        const data = await res.json();

        if (!res.ok) {
            throw data;
        }

        document.getElementById("missatge").innerText =
            "✅ Reserva creada correctament";
        carregarReserves();
    })
    .catch(err => {
        let missatge = "Error desconegut";

        if (err?.detail) {
            if (Array.isArray(err.detail)) {
                missatge = err.detail.map(e => e.msg).join(" | ");
            } else {
                missatge = err.detail;
            }
        }

        document.getElementById("missatge").innerText =
            "❌ " + missatge;
    });
}

function carregarReserves() {
    fetch(`${API_URL}/reserves`)
        .then(res => res.json())
        .then(data => {
            const llista = document.getElementById("llista");
            llista.innerHTML = "";

            data.forEach(r => {
                const li = document.createElement("li");
                li.innerText = `${r.servei} | ${r.data} | ${r.hora_inici} - ${r.hora_fi}`;
                llista.appendChild(li);
            });
        });
}
