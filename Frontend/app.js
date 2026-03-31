const state = {
    token: localStorage.getItem("helpdesk_token") || "",
    user: JSON.parse(localStorage.getItem("helpdesk_user") || "null"),
    currentView: "dashboard",
    tickets: [],
    ticketMeta: { total: 0, page: 1, pages: 1, per_page: 10 },
    selectedTicketId: null,
    selectedTicket: null,
    agents: [],
    adminStats: null,
    adminUsers: [],
    adminTickets: [],
    filters: { status: "", priority: "", search: "", page: 1 },
};

const STATUS_OPTIONS = ["open", "in_progress", "resolved", "closed"];
const PRIORITY_OPTIONS = ["low", "medium", "high", "critical"];
const ROLE_OPTIONS = ["user", "agent", "admin"];

const authView = document.getElementById("authView");
const appView = document.getElementById("appView");
const flash = document.getElementById("flash");
const currentUserBadge = document.getElementById("currentUserBadge");
const logoutButton = document.getElementById("logoutButton");
const adminNavButton = document.getElementById("adminNavButton");
const summaryCards = document.getElementById("summaryCards");
const dashboardContent = document.getElementById("dashboardContent");
const ticketList = document.getElementById("ticketList");
const ticketListMeta = document.getElementById("ticketListMeta");
const ticketPagination = document.getElementById("ticketPagination");
const ticketDetail = document.getElementById("ticketDetail");
const adminStats = document.getElementById("adminStats");
const adminUsersBody = document.getElementById("adminUsersBody");
const adminTicketSnapshot = document.getElementById("adminTicketSnapshot");
const heroTitle = document.getElementById("heroTitle");
const heroSubtitle = document.getElementById("heroSubtitle");

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function humanize(value) {
    return String(value ?? "")
        .replaceAll("_", " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
    if (!value) return "Not set";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function showMessage(message, type = "success") {
    flash.textContent = message;
    flash.className = `flash ${type}`;
}

function clearMessage() {
    flash.textContent = "";
    flash.className = "flash hidden";
}

async function api(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (state.token) headers.Authorization = `Bearer ${state.token}`;

    const response = await fetch(path, { ...options, headers });
    const payload = await response.json().catch(() => ({ success: false, message: "Unexpected server response." }));

    if (!response.ok || payload.success === false) {
        const error = new Error(payload.message || "Request failed.");
        error.status = response.status;
        throw error;
    }
    return payload;
}

function persistSession() {
    if (state.token && state.user) {
        localStorage.setItem("helpdesk_token", state.token);
        localStorage.setItem("helpdesk_user", JSON.stringify(state.user));
        return;
    }
    localStorage.removeItem("helpdesk_token");
    localStorage.removeItem("helpdesk_user");
}

function isAdmin() {
    return state.user?.role === "admin";
}

function isAgent() {
    return state.user?.role === "agent" || state.user?.role === "admin";
}

function updateChrome() {
    const authenticated = Boolean(state.user && state.token);
    authView.classList.toggle("hidden", authenticated);
    appView.classList.toggle("hidden", !authenticated);
    logoutButton.classList.toggle("hidden", !authenticated);
    currentUserBadge.classList.toggle("hidden", !authenticated);
    adminNavButton.classList.toggle("hidden", !isAdmin());

    if (authenticated) {
        currentUserBadge.textContent = `${state.user.username} - ${humanize(state.user.role)}`;
        heroTitle.textContent = isAdmin()
            ? "Manage support, staffing, and triage from one link."
            : "Stay on top of tickets from one browser workspace.";
        heroSubtitle.textContent = isAdmin()
            ? "Admins can view stats, manage users, and inspect ticket workload in the same interface."
            : "Create tickets, track progress, and collaborate on each issue without switching tools.";
    }
}

function setSession(token, user) {
    state.token = token;
    state.user = user;
    persistSession();
    updateChrome();
}

function clearSession() {
    state.token = "";
    state.user = null;
    state.tickets = [];
    state.selectedTicket = null;
    state.selectedTicketId = null;
    state.adminStats = null;
    state.adminUsers = [];
    state.adminTickets = [];
    persistSession();
    updateChrome();
}

function setView(viewName) {
    state.currentView = viewName;
    document.querySelectorAll(".view-section").forEach((section) => {
        section.classList.toggle("hidden", section.id !== `${viewName}Section`);
    });
    document.querySelectorAll(".nav-button").forEach((button) => {
        button.classList.toggle("active", button.dataset.view === viewName);
    });
}

function renderSummaryCards() {
    const cards = isAdmin() && state.adminStats
        ? [
            ["Tickets", state.adminStats.tickets.total],
            ["Open", state.adminStats.tickets.open],
            ["In Progress", state.adminStats.tickets.in_progress],
            ["Users", state.adminStats.users.total],
        ]
        : [
            ["Visible Tickets", state.tickets.length],
            ["Total Tickets", state.ticketMeta.total],
            ["Role", humanize(state.user?.role || "guest")],
            ["Page", `${state.ticketMeta.page}/${state.ticketMeta.pages}`],
        ];

    summaryCards.innerHTML = cards.map(([label, value]) => `
        <article class="summary-card dark">
            <span class="label">${escapeHtml(label)}</span>
            <span class="value">${escapeHtml(value)}</span>
        </article>
    `).join("");
}

function renderDashboard() {
    const cards = [`
        <article class="info-card">
            <h4>Account</h4>
            <p><strong>${escapeHtml(state.user?.username || "")}</strong></p>
            <p>${escapeHtml(state.user?.email || "")}</p>
            <p>Role: ${escapeHtml(humanize(state.user?.role || ""))}</p>
        </article>
    `, `
        <article class="info-card">
            <h4>Ticket Snapshot</h4>
            <p>Total tickets in current query: <strong>${escapeHtml(state.ticketMeta.total)}</strong></p>
            <p>Current page: ${escapeHtml(state.ticketMeta.page)} of ${escapeHtml(state.ticketMeta.pages)}</p>
            <p>Selected ticket: ${state.selectedTicket ? escapeHtml(state.selectedTicket.title) : "None selected"}</p>
        </article>
    `];

    cards.push(isAdmin() && state.adminStats ? `
        <article class="info-card">
            <h4>Admin Capacity</h4>
            <p>Unassigned active tickets: <strong>${escapeHtml(state.adminStats.unassigned)}</strong></p>
            <p>Agents: ${escapeHtml(state.adminStats.users.agents)}</p>
            <p>Total comments: ${escapeHtml(state.adminStats.total_comments)}</p>
        </article>
    ` : `
        <article class="info-card">
            <h4>Quick Start</h4>
            <p>Open Tickets to reply, update status, or inspect request history.</p>
            <p>Use Create Ticket to log a new issue directly from the browser.</p>
        </article>
    `);

    dashboardContent.innerHTML = cards.join("");
}

function renderTicketList() {
    ticketListMeta.textContent = `Showing page ${state.ticketMeta.page} of ${state.ticketMeta.pages}. ${state.ticketMeta.total} matching ticket(s).`;

    if (!state.tickets.length) {
        ticketList.innerHTML = `<div class="ticket-item"><h4>No tickets found</h4><p>Try different filters or create a new ticket.</p></div>`;
        ticketPagination.innerHTML = "";
        return;
    }

    ticketList.innerHTML = state.tickets.map((ticket) => `
        <article class="ticket-item ${ticket.id === state.selectedTicketId ? "active" : ""}" data-ticket-id="${escapeHtml(ticket.id)}">
            <div class="pill-row">
                <span class="pill status-${escapeHtml(ticket.status)}">${escapeHtml(humanize(ticket.status))}</span>
                <span class="pill priority-${escapeHtml(ticket.priority)}">${escapeHtml(humanize(ticket.priority))}</span>
            </div>
            <h4>${escapeHtml(ticket.title)}</h4>
            <p>${escapeHtml(ticket.description).slice(0, 140)}${ticket.description.length > 140 ? "..." : ""}</p>
            <div class="meta-row">
                <span>By ${escapeHtml(ticket.created_by_username || "Unknown")}</span>
                <span>${escapeHtml(ticket.comment_count || 0)} comments</span>
            </div>
        </article>
    `).join("");

    ticketPagination.innerHTML = `
        <button type="button" class="ghost-button" data-page-action="prev" ${state.ticketMeta.page <= 1 ? "disabled" : ""}>Previous</button>
        <button type="button" class="ghost-button" data-page-action="next" ${state.ticketMeta.page >= state.ticketMeta.pages ? "disabled" : ""}>Next</button>
    `;
}

function renderTicketDetail() {
    if (!state.selectedTicket) {
        ticketDetail.className = "detail-card empty-state";
        ticketDetail.textContent = "Select a ticket to view details.";
        return;
    }

    const ticket = state.selectedTicket;
    const assigneeOptions = [`<option value="">Unassigned</option>`]
        .concat(state.agents.map((agent) => `<option value="${escapeHtml(agent.id)}" ${ticket.assigned_to === agent.id ? "selected" : ""}>${escapeHtml(agent.username)}</option>`))
        .join("");
    const statusOptions = STATUS_OPTIONS.map((status) => `<option value="${status}" ${ticket.status === status ? "selected" : ""}>${humanize(status)}</option>`).join("");
    const priorityOptions = PRIORITY_OPTIONS.map((priority) => `<option value="${priority}" ${ticket.priority === priority ? "selected" : ""}>${humanize(priority)}</option>`).join("");
    const canUserClose = !isAgent() && ticket.status !== "closed";
    const managementForm = isAgent() ? `
        <form id="ticketUpdateForm" class="stack-form">
            <div class="two-column">
                <label>Status<select name="status">${statusOptions}</select></label>
                <label>Priority<select name="priority">${priorityOptions}</select></label>
            </div>
            <label>Assignee<select name="assigned_to">${assigneeOptions}</select></label>
            <button type="submit">Save Ticket Changes</button>
        </form>
    ` : canUserClose ? `
        <form id="ticketUpdateForm" class="stack-form">
            <input type="hidden" name="status" value="closed">
            <button type="submit">Close This Ticket</button>
        </form>
    ` : "";

    const comments = (ticket.comments || []).map((comment) => `
        <article class="comment-card ${comment.is_internal ? "internal" : ""}">
            <div class="comment-head">
                <span>${escapeHtml(comment.author_username || "Unknown")} - ${escapeHtml(humanize(comment.author_role || "user"))}</span>
                <span>${escapeHtml(formatDate(comment.created_at))}</span>
            </div>
            ${comment.is_internal ? `<div class="pill-row"><span class="pill priority-medium">Internal Note</span></div>` : ""}
            <p>${escapeHtml(comment.message)}</p>
        </article>
    `).join("") || `<div class="comment-card"><p>No comments yet.</p></div>`;

    ticketDetail.className = "detail-card";
    ticketDetail.innerHTML = `
        <div class="detail-meta">
            <span class="pill status-${escapeHtml(ticket.status)}">${escapeHtml(humanize(ticket.status))}</span>
            <span class="pill priority-${escapeHtml(ticket.priority)}">${escapeHtml(humanize(ticket.priority))}</span>
            <span class="pill">${escapeHtml(ticket.category || "General")}</span>
        </div>
        <h3>${escapeHtml(ticket.title)}</h3>
        <p>${escapeHtml(ticket.description)}</p>
        <div class="meta-row">
            <span>Created by ${escapeHtml(ticket.created_by_username || "Unknown")}</span>
            <span>Assigned to ${escapeHtml(ticket.assigned_to_username || "Nobody")}</span>
        </div>
        <div class="meta-row">
            <span>Created ${escapeHtml(formatDate(ticket.created_at))}</span>
            <span>Updated ${escapeHtml(formatDate(ticket.updated_at))}</span>
            <span>Resolved ${escapeHtml(formatDate(ticket.resolved_at))}</span>
        </div>
        <div class="detail-actions">
            ${managementForm}
            <form id="commentForm" class="stack-form">
                <label>
                    Add comment
                    <textarea name="message" rows="4" placeholder="Write an update or reply" required></textarea>
                </label>
                ${isAgent() ? `<label class="checkbox-row"><input type="checkbox" name="is_internal"><span>Mark as internal note</span></label>` : ""}
                <button type="submit">Post Comment</button>
            </form>
            <div class="comment-feed">${comments}</div>
        </div>
    `;
}

function renderAdmin() {
    if (!isAdmin()) return;

    if (state.adminStats) {
        const cards = [
            ["Open Tickets", state.adminStats.tickets.open],
            ["In Progress", state.adminStats.tickets.in_progress],
            ["Resolved", state.adminStats.tickets.resolved],
            ["Unassigned", state.adminStats.unassigned],
            ["Agents", state.adminStats.users.agents],
            ["Users", state.adminStats.users.users],
        ];
        adminStats.innerHTML = cards.map(([label, value]) => `
            <article class="summary-card">
                <span class="label">${escapeHtml(label)}</span>
                <span class="value">${escapeHtml(value)}</span>
            </article>
        `).join("");
    }

    adminUsersBody.innerHTML = state.adminUsers.map((user) => `
        <tr>
            <td><strong>${escapeHtml(user.username)}</strong><br><span>${escapeHtml(user.email)}</span></td>
            <td><select data-user-role="${escapeHtml(user.id)}">${ROLE_OPTIONS.map((role) => `<option value="${role}" ${user.role === role ? "selected" : ""}>${humanize(role)}</option>`).join("")}</select></td>
            <td>${user.is_active ? "Active" : "Inactive"}</td>
            <td>${escapeHtml(user.ticket_count || 0)}</td>
            <td>
                <div class="action-row">
                    <button type="button" data-user-save="${escapeHtml(user.id)}">Save Role</button>
                    <button type="button" class="ghost-button" data-user-toggle="${escapeHtml(user.id)}">${user.is_active ? "Deactivate" : "Activate"}</button>
                </div>
            </td>
        </tr>
    `).join("") || `<tr><td colspan="5">No users found.</td></tr>`;

    adminTicketSnapshot.innerHTML = state.adminTickets.map((ticket) => `
        <article class="snapshot-item">
            <div class="pill-row">
                <span class="pill status-${escapeHtml(ticket.status)}">${escapeHtml(humanize(ticket.status))}</span>
                <span class="pill priority-${escapeHtml(ticket.priority)}">${escapeHtml(humanize(ticket.priority))}</span>
            </div>
            <h4>${escapeHtml(ticket.title)}</h4>
            <p>${escapeHtml(ticket.created_by_username || "Unknown")}</p>
        </article>
    `).join("") || `<div class="snapshot-item">No tickets available.</div>`;
}

async function loadTicketDetail(ticketId) {
    const payload = await api(`/api/tickets/${ticketId}`);
    state.selectedTicketId = ticketId;
    state.selectedTicket = payload.data.ticket;
    state.agents = payload.data.agents || [];
    renderTicketList();
    renderTicketDetail();
}

async function loadTickets(keepSelection = true) {
    const params = new URLSearchParams({ page: String(state.filters.page) });
    if (state.filters.status) params.set("status", state.filters.status);
    if (state.filters.priority) params.set("priority", state.filters.priority);
    if (state.filters.search) params.set("search", state.filters.search);

    const payload = await api(`/api/tickets/?${params.toString()}`);
    state.tickets = payload.data.tickets || [];
    state.ticketMeta = payload.data;
    renderTicketList();

    if (!keepSelection) {
        state.selectedTicketId = null;
        state.selectedTicket = null;
    }

    if (state.selectedTicketId && state.tickets.some((ticket) => ticket.id === state.selectedTicketId)) {
        await loadTicketDetail(state.selectedTicketId);
        return;
    }

    if (state.tickets.length) {
        await loadTicketDetail(state.tickets[0].id);
        return;
    }

    state.selectedTicket = null;
    renderTicketDetail();
}

async function loadAdminData() {
    if (!isAdmin()) return;

    const [statsPayload, usersPayload, ticketsPayload] = await Promise.all([
        api("/api/admin/stats"),
        api("/api/admin/users?page=1"),
        api("/api/admin/tickets?page=1&limit=12"),
    ]);

    state.adminStats = statsPayload.data;
    state.adminUsers = usersPayload.data.users || [];
    state.adminTickets = ticketsPayload.data.tickets || [];
    renderAdmin();
}

async function refreshWorkspace() {
    clearMessage();
    await loadTickets();
    if (isAdmin()) await loadAdminData();
    renderSummaryCards();
    renderDashboard();
}

async function handleAuthSuccess(token, user, message) {
    setSession(token, user);
    setView("dashboard");
    await refreshWorkspace();
    showMessage(message);
}

async function handleLogin(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
        const payload = await api("/api/auth/login", {
            method: "POST",
            body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
        });
        await handleAuthSuccess(payload.data.token, payload.data.user, payload.message);
        event.currentTarget.reset();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
        const payload = await api("/api/auth/register", {
            method: "POST",
            body: JSON.stringify({
                username: form.get("username"),
                email: form.get("email"),
                password: form.get("password"),
            }),
        });
        await handleAuthSuccess(payload.data.token, payload.data.user, payload.message);
        event.currentTarget.reset();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function handleCreateTicket(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
        const payload = await api("/api/tickets/", {
            method: "POST",
            body: JSON.stringify({
                title: form.get("title"),
                description: form.get("description"),
                priority: form.get("priority"),
                category: form.get("category"),
            }),
        });
        showMessage(payload.message);
        event.currentTarget.reset();
        state.filters.page = 1;
        setView("tickets");
        await loadTickets(false);
        if (payload.data.ticket?.id) await loadTicketDetail(payload.data.ticket.id);
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function handleTicketUpdate(event) {
    event.preventDefault();
    if (!state.selectedTicketId) return;

    const form = new FormData(event.currentTarget);
    const payload = {};
    if (form.get("status")) payload.status = form.get("status");
    if (form.get("priority")) payload.priority = form.get("priority");
    if (event.currentTarget.querySelector("[name='assigned_to']")) payload.assigned_to = form.get("assigned_to");

    try {
        const response = await api(`/api/tickets/${state.selectedTicketId}`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });
        showMessage(response.message);
        await loadTickets();
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function handleCommentSubmit(event) {
    event.preventDefault();
    if (!state.selectedTicketId) return;

    const form = new FormData(event.currentTarget);
    try {
        const response = await api(`/api/tickets/${state.selectedTicketId}/comments`, {
            method: "POST",
            body: JSON.stringify({
                message: form.get("message"),
                is_internal: form.get("is_internal") === "on",
            }),
        });
        showMessage(response.message);
        event.currentTarget.reset();
        await loadTickets();
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function handleAdminAction(event) {
    const saveId = event.target.dataset.userSave;
    const toggleId = event.target.dataset.userToggle;
    if (!saveId && !toggleId) return;

    try {
        if (saveId) {
            const select = document.querySelector(`[data-user-role="${saveId}"]`);
            const response = await api(`/api/admin/users/${saveId}/role`, {
                method: "PUT",
                body: JSON.stringify({ role: select.value }),
            });
            showMessage(response.message);
        }
        if (toggleId) {
            const response = await api(`/api/admin/users/${toggleId}/toggle`, {
                method: "PUT",
                body: JSON.stringify({}),
            });
            showMessage(response.message);
        }
        await loadAdminData();
        await loadTickets();
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function restoreSession() {
    if (!state.token) {
        updateChrome();
        return;
    }
    try {
        const payload = await api("/api/auth/me");
        state.user = payload.data.user;
        persistSession();
        updateChrome();
        await refreshWorkspace();
    } catch {
        clearSession();
        showMessage("Session expired. Please log in again.", "error");
    }
}

function logout() {
    clearSession();
    setView("dashboard");
    ticketList.innerHTML = "";
    ticketDetail.innerHTML = "";
    adminStats.innerHTML = "";
    adminUsersBody.innerHTML = "";
    adminTicketSnapshot.innerHTML = "";
    clearMessage();
}

document.getElementById("loginForm").addEventListener("submit", handleLogin);
document.getElementById("registerForm").addEventListener("submit", handleRegister);
document.getElementById("createTicketForm").addEventListener("submit", handleCreateTicket);
document.getElementById("refreshDashboardButton").addEventListener("click", refreshWorkspace);
document.getElementById("refreshTicketsButton").addEventListener("click", refreshWorkspace);
document.getElementById("refreshAdminButton").addEventListener("click", async () => {
    try {
        await loadAdminData();
        renderSummaryCards();
        renderDashboard();
        showMessage("Admin data refreshed.");
    } catch (error) {
        showMessage(error.message, "error");
    }
});
document.getElementById("clearFiltersButton").addEventListener("click", async () => {
    document.getElementById("ticketFiltersForm").reset();
    state.filters = { status: "", priority: "", search: "", page: 1 };
    try {
        await loadTickets(false);
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
});
document.getElementById("ticketFiltersForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    state.filters.status = String(form.get("status") || "");
    state.filters.priority = String(form.get("priority") || "");
    state.filters.search = String(form.get("search") || "").trim();
    state.filters.page = 1;
    try {
        await loadTickets(false);
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
});
logoutButton.addEventListener("click", logout);

document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", async () => {
        setView(button.dataset.view);
        if (button.dataset.view === "admin") {
            try {
                await loadAdminData();
                renderSummaryCards();
                renderDashboard();
            } catch (error) {
                showMessage(error.message, "error");
            }
        }
    });
});

ticketList.addEventListener("click", async (event) => {
    const card = event.target.closest("[data-ticket-id]");
    if (!card) return;
    try {
        await loadTicketDetail(card.dataset.ticketId);
    } catch (error) {
        showMessage(error.message, "error");
    }
});

ticketPagination.addEventListener("click", async (event) => {
    const action = event.target.dataset.pageAction;
    if (!action) return;
    if (action === "prev" && state.filters.page > 1) state.filters.page -= 1;
    if (action === "next" && state.filters.page < state.ticketMeta.pages) state.filters.page += 1;
    try {
        await loadTickets(false);
        renderSummaryCards();
        renderDashboard();
    } catch (error) {
        showMessage(error.message, "error");
    }
});

ticketDetail.addEventListener("submit", async (event) => {
    if (event.target.id === "ticketUpdateForm") await handleTicketUpdate(event);
    if (event.target.id === "commentForm") await handleCommentSubmit(event);
});
adminUsersBody.addEventListener("click", handleAdminAction);

updateChrome();
setView("dashboard");
restoreSession();
