import { createPinia } from 'pinia'
import { auth } from "./auth.module";

export default createPinia({
    modules: {
        auth,
    },
})
