document.addEventListener('DOMContentLoaded', function() {
    const timelineBody = document.getElementById('timeline-body');
    
    if (!timelineEvents || timelineEvents.length === 0) {
        timelineBody.innerHTML = '<tr><td colspan="7" class="text-center p-4">No timeline events found</td></tr>';
        return;
    }
    
    // Group events by timestamp and create rows
    const eventsByTimestamp = {};
    
    timelineEvents.forEach(event => {
        const timestamp = event.timestamp;
        if (!eventsByTimestamp[timestamp]) {
            eventsByTimestamp[timestamp] = [];
        }
        eventsByTimestamp[timestamp].push(event);
    });
    
    // Sort timestamps
    const sortedTimestamps = Object.keys(eventsByTimestamp).sort((a, b) => {
        return new Date(a) - new Date(b);
    });
    
    // Create table rows
    sortedTimestamps.forEach(timestamp => {
        const events = eventsByTimestamp[timestamp];
        const row = createTimelineRow(timestamp, events);
        timelineBody.appendChild(row);
    });
});

function createTimelineRow(timestamp, events) {
    const row = document.createElement('tr');
    
    // Parse timestamp
    const date = new Date(timestamp);
    const dateStr = formatDate(date);
    const timeStr = formatTime(date);
    
    // Timeline column
    const timelineCell = document.createElement('td');
    timelineCell.className = 'timeline-col';
    timelineCell.innerHTML = `
        <span class="timestamp">
            <span class="timestamp-date">${dateStr}</span>
            <span class="timestamp-time">${timeStr}</span>
        </span>
    `;
    row.appendChild(timelineCell);
    
    // Notes column
    const notesCell = document.createElement('td');
    notesCell.className = 'notes-col';
    const noteEvents = events.filter(e => e.type === 'note');
    if (noteEvents.length > 0) {
        noteEvents.forEach(note => {
            const noteDiv = document.createElement('div');
            noteDiv.className = 'event-note';
            const authorName = note.data.author || 'Unknown';
            const authorEmail = note.data.email || '';
            const authorDisplay = authorEmail ? `${authorName} (${authorEmail})` : authorName;
            noteDiv.innerHTML = `
                <div class="event-note-author">${escapeHtml(authorDisplay)}</div>
                <div class="event-note-content">${escapeHtml(note.data.content || '')}</div>
            `;
            notesCell.appendChild(noteDiv);
        });
    } else {
        notesCell.innerHTML = '<span class="empty-cell">-</span>';
    }
    row.appendChild(notesCell);
    
    // Orders column
    const ordersCell = document.createElement('td');
    ordersCell.className = 'orders-col';
    const orderEvents = events.filter(e => e.type === 'order');
    if (orderEvents.length > 0) {
        orderEvents.forEach(order => {
            const orderDiv = document.createElement('div');
            orderDiv.className = 'event-order';
            const action = order.data.action || 'created';
            const actionText = action === 'created' ? 'Ordered' : action === 'updated' ? 'Updated' : 'Discontinued';
            const email = order.data.email || '';
            const emailDisplay = email ? `<div class="event-email">${escapeHtml(email)}</div>` : '';
            orderDiv.innerHTML = `
                <div class="event-order-action">${actionText}</div>
                <div>${escapeHtml(order.data.investigation || '')}</div>
                ${emailDisplay}
            `;
            ordersCell.appendChild(orderDiv);
        });
    } else {
        ordersCell.innerHTML = '<span class="empty-cell">-</span>';
    }
    row.appendChild(ordersCell);
    
    // Lab Reports column
    const labsCell = document.createElement('td');
    labsCell.className = 'labs-col';
    const labEvents = events.filter(e => e.type === 'lab');
    if (labEvents.length > 0) {
        labEvents.forEach(lab => {
            const labDiv = document.createElement('div');
            labDiv.className = 'event-lab';
            let html = `<div class="event-lab-name">${escapeHtml(lab.data.test || '')}</div>`;
            if (lab.data.email) {
                html += `<div class="event-email">${escapeHtml(lab.data.email)}</div>`;
            }
            if (lab.data.reportedAt) {
                html += `<div class="event-lab-reported">Reported: ${escapeHtml(lab.data.reportedAt)}</div>`;
            }
            if (lab.data.results && lab.data.results.length > 0) {
                html += `<div class="event-lab-results">${lab.data.results.map(r => escapeHtml(r)).join('<br>')}</div>`;
            }
            labDiv.innerHTML = html;
            labsCell.appendChild(labDiv);
        });
    } else {
        labsCell.innerHTML = '<span class="empty-cell">-</span>';
    }
    row.appendChild(labsCell);
    
    // Vitals column
    const vitalsCell = document.createElement('td');
    vitalsCell.className = 'vitals-col';
    const vitalEvents = events.filter(e => e.type === 'vital');
    if (vitalEvents.length > 0) {
        vitalEvents.forEach(vital => {
            const vitalDiv = document.createElement('div');
            vitalDiv.className = 'event-vital';
            const vitalData = vital.data;
            let html = '';
            // Show email first if available
            if (vitalData.email) {
                html += `<div class="event-email">${escapeHtml(vitalData.email)}</div>`;
            }
            if (vitalData.temp) html += `<div class="event-vital-item"><span class="event-vital-label">Temp:</span>${escapeHtml(vitalData.temp)}</div>`;
            if (vitalData.hr) html += `<div class="event-vital-item"><span class="event-vital-label">HR:</span>${escapeHtml(vitalData.hr)}</div>`;
            if (vitalData.rr) html += `<div class="event-vital-item"><span class="event-vital-label">RR:</span>${escapeHtml(vitalData.rr)}</div>`;
            if (vitalData.bp) html += `<div class="event-vital-item"><span class="event-vital-label">BP:</span>${escapeHtml(vitalData.bp)}</div>`;
            if (vitalData.map) html += `<div class="event-vital-item"><span class="event-vital-label">MAP:</span>${escapeHtml(vitalData.map)}</div>`;
            if (vitalData.cvp) html += `<div class="event-vital-item"><span class="event-vital-label">CVP:</span>${escapeHtml(vitalData.cvp)}</div>`;
            if (vitalData.spo2) html += `<div class="event-vital-item"><span class="event-vital-label">SpO2:</span>${escapeHtml(vitalData.spo2)}</div>`;
            if (vitalData.fio2) html += `<div class="event-vital-item"><span class="event-vital-label">FiO2:</span>${escapeHtml(vitalData.fio2)}</div>`;
            if (vitalData.gcs) html += `<div class="event-vital-item"><span class="event-vital-label">GCS:</span>${escapeHtml(vitalData.gcs)}</div>`;
            if (vitalData.avpu) html += `<div class="event-vital-item"><span class="event-vital-label">AVPU:</span>${escapeHtml(vitalData.avpu)}</div>`;
            if (vitalData.position) html += `<div class="event-vital-item"><span class="event-vital-label">Position:</span>${escapeHtml(vitalData.position)}</div>`;
            vitalDiv.innerHTML = html || '<span class="empty-cell">-</span>';
            vitalsCell.appendChild(vitalDiv);
        });
    } else {
        vitalsCell.innerHTML = '<span class="empty-cell">-</span>';
    }
    row.appendChild(vitalsCell);
    
    // Input/Output column
    const ioCell = document.createElement('td');
    ioCell.className = 'io-col';
    const ioEvents = events.filter(e => e.type === 'io');
    if (ioEvents.length > 0) {
        ioEvents.forEach(io => {
            const ioDiv = document.createElement('div');
            ioDiv.className = 'event-io';
            let html = '';
            if (io.data.input) {
                html += `<div class="event-io-input"><span class="event-io-label">Input:</span>${escapeHtml(io.data.input)}</div>`;
            }
            if (io.data.output) {
                html += `<div class="event-io-output"><span class="event-io-label">Output:</span>${escapeHtml(io.data.output)}</div>`;
            }
            ioDiv.innerHTML = html || '<span class="empty-cell">-</span>';
            ioCell.appendChild(ioDiv);
        });
    } else {
        ioCell.innerHTML = '<span class="empty-cell">-</span>';
    }
    row.appendChild(ioCell);
    
    // Unaddressed Events column (empty for individual rows, analysis shown separately)
    const analysisCell = document.createElement('td');
    analysisCell.className = 'analysis-col';
    analysisCell.innerHTML = '<span class="empty-cell">-</span>';
    row.appendChild(analysisCell);
    
    return row;
}

function formatDate(date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
}

function formatTime(date) {
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    const minutesStr = minutes < 10 ? '0' + minutes : minutes;
    return `${hours}:${minutesStr} ${ampm}`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

