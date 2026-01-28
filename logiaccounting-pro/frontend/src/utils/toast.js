/**
 * Toast notification utility.
 * Usage:
 *   import toast from '../utils/toast';
 *   toast.success('Item saved');
 *   toast.error('Something went wrong');
 *   toast.warning('Low stock');
 *   toast.info('Processing...');
 */

let _counter = 0;

function _dispatch(type, message) {
  _counter += 1;
  window.dispatchEvent(
    new CustomEvent('show-toast', {
      detail: { id: `toast-${_counter}-${Date.now()}`, type, message },
    })
  );
}

const toast = (message) => _dispatch('info', message);
toast.success = (message) => _dispatch('success', message);
toast.error = (message) => _dispatch('error', message);
toast.warning = (message) => _dispatch('warning', message);
toast.info = (message) => _dispatch('info', message);

export default toast;
