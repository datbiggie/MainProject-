// page-data.js: lee valores inyectados en el DOM por la plantilla y los expone en window.
(function(){
	try {
		var el = document.getElementById('page-data');
		var info = {
			account_type: 'usuario',
			user_id: '',
			is_authenticated: false
		};

		if (el) {
			info.account_type = el.getAttribute('data-account-type') || info.account_type;
			info.user_id = el.getAttribute('data-user-id') || info.user_id;
			info.is_authenticated = el.getAttribute('data-authenticated') === '1';
		}

		window.USER_INFO = info;

		// CSRF token: prefer meta tag si existe
		var meta = document.querySelector('meta[name=csrf-token]');
		if (meta && meta.content) {
			window.CSRF_TOKEN = meta.content;
		} else if (el && el.getAttribute('data-csrf')) {
			window.CSRF_TOKEN = el.getAttribute('data-csrf');
		} else {
			window.CSRF_TOKEN = '';
		}
	} catch (err) {
		console.error('page-data.js error', err);
	}
})();
