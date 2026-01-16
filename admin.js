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

        events: await carregarReserves(),

        eventMouseEnter: function(info) {
            const tooltip = document.createElement("div");
            tooltip.className = "fc-tooltip";
            tooltip.innerHTML = `
                <strong>${info.event.title}</strong><br>
                🕒 ${info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                – ${info.event.end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            `;

            document.body.appendChild(tooltip);

            info.el.addEventListener("mousemove", function(e) {
                tooltip.style.left = e.pageX + 10 + "px";
                tooltip.style.top = e.pageY + 10 + "px";
            });

            info.el.addEventListener("mouseleave", function() {
                tooltip.remove();
            });
        },

        eventDidMount: function(info) {
            info.el.addEventListener("dblclick", function() {
                alert(
                    "Servei i usuari: " + info.event.title + "\n" +
                    "Inici: " + info.event.start.toLocaleString() + "\n" +
                    "Fi: " + info.event.end.toLocaleString()
                );
            });
        }
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
