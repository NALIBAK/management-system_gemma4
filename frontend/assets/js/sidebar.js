/* ============================================================
   Shared Sidebar HTML — injected by sidebar.js
   ============================================================ */

function renderSidebar(activePage) {
    const userRole = auth.getUser()?.role || 'guest';
    const nav = [
        {
            label: 'Main', items: [
                { href: '../dashboard.html', icon: '🏠', text: 'Dashboard', id: 'dashboard', roles: ['super_admin', 'admin', 'hod', 'staff'] },
                { href: '../students/index.html', icon: '👨‍🎓', text: 'Students', id: 'students', roles: ['super_admin', 'admin', 'hod', 'staff'] },
                { href: '../staff/index.html', icon: '👨‍🏫', text: 'Staff', id: 'staff', roles: ['super_admin', 'admin', 'hod'] },
                { href: '../staff/allocations.html', icon: '📖', text: 'Class Allocations', id: 'allocations', roles: ['super_admin', 'admin', 'hod', 'staff'] },
            ]
        },
        {
            label: 'Academics', items: [
                { href: '../departments/index.html', icon: '🏛️', text: 'Departments', id: 'departments', roles: ['super_admin', 'admin'] },
                { href: '../courses/index.html', icon: '📚', text: 'Courses', id: 'courses', roles: ['super_admin', 'admin'] },
                { href: '../timetable/index.html', icon: '🗓️', text: 'Timetable', id: 'timetable', roles: ['super_admin', 'admin', 'hod', 'staff'] },
                { href: '../attendance/index.html', icon: '✅', text: 'Attendance', id: 'attendance', roles: ['super_admin', 'admin', 'hod', 'staff'] },
                { href: '../marks/index.html', icon: '📝', text: 'Marks & Results', id: 'marks', roles: ['super_admin', 'admin', 'hod', 'staff'] },
            ]
        },
        {
            label: 'Administration', items: [
                { href: '../fees/index.html', icon: '💰', text: 'Fees', id: 'fees', roles: ['super_admin', 'admin'] },
                { href: '../reports/index.html', icon: '📊', text: 'Reports', id: 'reports', roles: ['super_admin', 'admin', 'hod'] },
                { href: '../notifications/index.html', icon: '🔔', text: 'Notifications', id: 'notifications', roles: ['super_admin', 'admin', 'hod', 'staff'] },
            ]
        },
        {
            label: 'System', items: [
                { href: '../settings/index.html', icon: '⚙️', text: 'Settings', id: 'settings', roles: ['super_admin', 'admin'] },
            ]
        },
    ];

    const html = nav.map(section => {
        const filteredItems = section.items.filter(item => item.roles.includes(userRole));
        if (filteredItems.length === 0) return '';

        return `
    <div class="nav-section-label">${section.label}</div>
    ${filteredItems.map(item => `
      <a href="${item.href}" class="nav-item ${item.id === activePage ? 'active' : ''}">
        <span class="nav-icon">${item.icon}</span> ${item.text}
      </a>`).join('')}`;
    }).join('');

    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.querySelector('.sidebar-nav').innerHTML = html;
}

function renderHeader(title, subtitle = '') {
    const user = auth.getUser();
    const header = document.getElementById('page-header');
    if (header) {
        header.innerHTML = `
      <div>
        <div class="header-title">${title}</div>
        ${subtitle ? `<div class="header-subtitle">${subtitle}</div>` : ''}
      </div>
      <div class="header-actions">
        <button class="theme-toggle" onclick="theme.toggle()">🌙</button>
        <div class="avatar">${auth.getUserInitials()}</div>
        <span style="font-size:13px;color:var(--text-muted)">${user?.username || ''}</span>
        <button class="btn btn-ghost btn-sm" onclick="auth.logout()">Logout</button>
      </div>`;
    }
}

window.renderSidebar = renderSidebar;
window.renderHeader = renderHeader;
