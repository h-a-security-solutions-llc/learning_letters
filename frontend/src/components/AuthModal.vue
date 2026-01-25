<template>
  <div
    class="auth-overlay"
    role="dialog"
    aria-labelledby="auth-title"
    @click.self="$emit('close')"
  >
    <div class="auth-modal" role="document">
      <div class="auth-header">
        <h2 id="auth-title">
          {{ isLoginMode ? 'Sign In' : 'Create Account' }}
        </h2>
        <button class="close-button" aria-label="Close" @click="$emit('close')">
          <span aria-hidden="true">×</span>
        </button>
      </div>

      <div class="auth-content">
        <form @submit.prevent="handleSubmit">
          <!-- Display Name (Register only) -->
          <div v-if="!isLoginMode" class="form-group">
            <label for="display-name">Display Name</label>
            <input
              id="display-name"
              v-model="displayName"
              type="text"
              placeholder="Your name"
              required
              maxlength="100"
              :disabled="isLoading"
            >
          </div>

          <!-- Email -->
          <div class="form-group">
            <label for="email">Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              placeholder="your@email.com"
              required
              :disabled="isLoading"
            >
          </div>

          <!-- Password -->
          <div class="form-group">
            <label for="password">Password</label>
            <div class="password-input">
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter password"
                required
                minlength="8"
                :disabled="isLoading"
              >
              <button
                type="button"
                class="toggle-password"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? 'Hide' : 'Show' }}
              </button>
            </div>
            <p v-if="!isLoginMode" class="password-hint">
              8-50 characters with uppercase, lowercase, and a number
            </p>
          </div>

          <!-- Confirm Password (Register only) -->
          <div v-if="!isLoginMode" class="form-group">
            <label for="confirm-password">Confirm Password</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Confirm password"
              required
              :disabled="isLoading"
            >
          </div>

          <!-- Error Message -->
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <!-- Submit Button -->
          <button type="submit" class="submit-button" :disabled="isLoading || !isFormValid">
            <span v-if="isLoading" class="loading-spinner" />
            {{ isLoading ? 'Please wait...' : (isLoginMode ? 'Sign In' : 'Create Account') }}
          </button>
        </form>

        <!-- Mode Toggle -->
        <div class="mode-toggle">
          <span>{{ isLoginMode ? "Don't have an account?" : 'Already have an account?' }}</span>
          <button type="button" class="toggle-mode" @click="toggleMode">
            {{ isLoginMode ? 'Sign Up' : 'Sign In' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'

export default {
  name: 'AuthModal',
  props: {
    initialMode: {
      type: String,
      default: 'login', // 'login' or 'register'
    },
  },
  emits: ['close', 'success'],
  setup(props, { emit }) {
    const { login, register, isLoading, error, clearError } = useAuth()

    const isLoginMode = ref(props.initialMode === 'login')
    const email = ref('')
    const password = ref('')
    const confirmPassword = ref('')
    const displayName = ref('')
    const showPassword = ref(false)
    const localError = ref('')

    // Combine local and auth errors
    const errorMessage = computed(() => localError.value || error.value)

    // Form validation
    const isFormValid = computed(() => {
      if (!email.value || !password.value) return false
      if (!isLoginMode.value) {
        if (!displayName.value.trim()) return false
        if (password.value !== confirmPassword.value) return false
        if (password.value.length < 8 || password.value.length > 50) return false
      }
      return true
    })

    // Clear errors when switching modes or changing input
    watch([isLoginMode, email, password, confirmPassword, displayName], () => {
      localError.value = ''
      clearError()
    })

    const toggleMode = () => {
      isLoginMode.value = !isLoginMode.value
      // Reset form
      password.value = ''
      confirmPassword.value = ''
      localError.value = ''
      clearError()
    }

    const handleSubmit = async () => {
      localError.value = ''
      clearError()

      // Client-side validation
      if (!isLoginMode.value) {
        if (password.value !== confirmPassword.value) {
          localError.value = 'Passwords do not match'
          return
        }
        if (password.value.length < 8) {
          localError.value = 'Password must be at least 8 characters'
          return
        }
        if (password.value.length > 50) {
          localError.value = 'Password must be at most 50 characters'
          return
        }
        if (!/[A-Z]/.test(password.value)) {
          localError.value = 'Password must contain an uppercase letter'
          return
        }
        if (!/[a-z]/.test(password.value)) {
          localError.value = 'Password must contain a lowercase letter'
          return
        }
        if (!/[0-9]/.test(password.value)) {
          localError.value = 'Password must contain a number'
          return
        }
      }

      try {
        if (isLoginMode.value) {
          await login(email.value, password.value)
        } else {
          await register(email.value, password.value, displayName.value.trim())
        }
        emit('success')
        emit('close')
      } catch {
        // Error is already set in the composable
      }
    }

    return {
      isLoginMode,
      email,
      password,
      confirmPassword,
      displayName,
      showPassword,
      errorMessage,
      isLoading,
      isFormValid,
      toggleMode,
      handleSubmit,
    }
  },
}
</script>

<style scoped>
.auth-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-modal {
  background: white;
  border-radius: 20px;
  max-width: 400px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px 20px 0 0;
}

.auth-header h2 {
  margin: 0;
  font-size: 1.4rem;
}

.close-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.auth-content {
  padding: 25px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
}

.form-group input {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #ddd;
  border-radius: 10px;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: #667eea;
  outline: none;
}

.form-group input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.password-input {
  position: relative;
  display: flex;
  align-items: center;
}

.password-input input {
  padding-right: 70px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #667eea;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  padding: 5px;
}

.toggle-password:hover {
  color: #764ba2;
}

.password-hint {
  margin: 8px 0 0 0;
  font-size: 0.8rem;
  color: #888;
}

.error-message {
  background: #fff0f0;
  color: #d32f2f;
  padding: 12px 15px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 0.9rem;
  border: 1px solid #ffcdd2;
}

.submit-button {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.mode-toggle {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  color: #666;
  font-size: 0.95rem;
}

.toggle-mode {
  background: none;
  border: none;
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  margin-left: 5px;
}

.toggle-mode:hover {
  color: #764ba2;
  text-decoration: underline;
}

@media (max-width: 480px) {
  .auth-modal {
    max-width: 100%;
    border-radius: 15px;
  }

  .auth-header {
    border-radius: 15px 15px 0 0;
  }

  .auth-content {
    padding: 20px;
  }
}
</style>
