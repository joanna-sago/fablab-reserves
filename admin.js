const API_URL = "https://fablab-backend-zk8n.onrender.com";

document.addEventListener("DOMContentLoaded", async function () {
    const calendarEl = document.getElementById("calendar");

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        locale: "ca",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek"
        },
        events: await carregarReserves()
    });

    calendar.render();
});

async function carregarReserves() {
    try {
        const response = await fetch(`${API_URL}/reserves`);
        const reserves = await response.json();

        return reserves.map(reserva => ({
            title: `${reserva.servei} – ${reserva.usuari_id}`,
            start: `${reserva.data}T${reserva.hora_inici}`,
            end: `${reserva.data}T${reserva.hora_fi}`
        }));

    } catch (error) {
        alert("Error carregant les reserves");
        return [];
    }
}
