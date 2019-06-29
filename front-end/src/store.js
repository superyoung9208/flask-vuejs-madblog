export default {
    debug: true,
    state: {
      is_new: false
    },
    setNewAction () {
      if (this.debug) { console.log('setNewAction triggered') }
      this.state.is_new = true
    },
    resetNotNewAction () {
      if (this.debug) { console.log('resetNotNewAction triggered') }
      this.state.is_new = false
    }
  }