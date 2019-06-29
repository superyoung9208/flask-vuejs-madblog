<template>
  <div class="container">
    <button type="button" class="btn btn-primary">{{ msg }}</button>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Ping',
  data() {
    return {
      msg: ''
    }
  },
  methods: {
    getMessage () {
      const path = 'http://localhost:5000/api/ping'
      axios.get(path)
        .then((res) => {
          console.log(res)
          this.msg = res.data['message'];
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        })
    }
  },
  created () {
    this.getMessage()
  }
}
</script>