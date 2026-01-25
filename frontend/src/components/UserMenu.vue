<template>
  <div class="user-menu" :class="{ open: isOpen }">
    <button class="user-button" :aria-expanded="isOpen" @click="toggleMenu">
      <span class="user-avatar">{{ avatarInitial }}</span>
      <span class="user-name">{{ displayName }}</span>
      <span class="dropdown-arrow">{{ isOpen ? '▲' : '▼' }}</span>
    </button>

    <div v-if="isOpen" class="dropdown-menu">
      <div class="user-info">
        <span class="user-email">{{ user?.email }}</span>
      </div>
      <div class="menu-divider" />
      <button class="menu-item" @click="handleLogout">
        <span class="menu-icon">🚪</span>
        Sign Out
      </button>
    </div>

    <!-- Backdrop to close menu when clicking outside -->
    <div v-if="isOpen" class="menu-backdrop" @click="isOpen = false" />
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

export default {
  name: 'UserMenu',
  emits: ['logout'],
  setup(_, { emit }) {
    const { user, logout, isLoading } = useAuth()
    const isOpen = ref(false)

    const displayName = computed(() => user.value?.display_name || 'User')
    const avatarInitial = computed(() => displayName.value.charAt(0).toUpperCase())

    const toggleMenu = () => {
      isOpen.value = !isOpen.value
    }

    const handleLogout = async () => {
      isOpen.value = false
      await logout()
      emit('logout')
    }

    return {
      user,
      isOpen,
      displayName,
      avatarInitial,
      isLoading,
      toggleMenu,
      handleLogout,
    }
  },
}
</script>

<style scoped>
.user-menu {
  position: relative;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 25px;
  padding: 6px 14px 6px 6px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.user-button:hover {
  background: white;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}

.user-name {
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-arrow {
  font-size: 0.6rem;
  color: #888;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  min-width: 200px;
  z-index: 100;
  animation: dropdownSlide 0.2s ease-out;
}

@keyframes dropdownSlide {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-info {
  padding: 15px;
}

.user-email {
  font-size: 0.85rem;
  color: #666;
  word-break: break-all;
}

.menu-divider {
  height: 1px;
  background: #eee;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 15px;
  background: none;
  border: none;
  text-align: left;
  font-size: 0.95rem;
  color: #333;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f5f5f5;
}

.menu-item:last-child {
  border-radius: 0 0 12px 12px;
}

.menu-icon {
  font-size: 1.1rem;
}

.menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
}

@media (max-width: 600px) {
  .user-name {
    display: none;
  }

  .user-button {
    padding: 6px;
  }

  .dropdown-arrow {
    display: none;
  }
}
</style>
