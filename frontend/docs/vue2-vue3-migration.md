// BEFORE MERGE: Is this documentation needed on the GitHub ? Should it be here ? 

# Vue 2 > Vue 3 migration notes

These are my notes on how to migrate between Vue 2 and Vue 3

This guide is only valid in the context of Vue 2 SFC using TypeScript with `vue-property-decorator`
It is mostly made of examples, I assume the reader read Vue's docs before to understand concepts.

## Components

### Migrating data

Vue 2 uses a simple syntax to create reactive data. This block would be in a `<script lang="ts">` tag 
```ts
@Component()
export default class MyComponent extends Vue {
    myData: boolean = false;
    
    myFunction() {
        myData = true;
    }
}
```

Vue 3 on the other hand uses ref declaration. The following block would be in a `<script setup lang="ts">` tag.
```ts
import { ref } from "vue";

const myData = ref<boolean>(false);

function myFunction() {
    myData.value = true;
}
```

### Migrating props

Vue 2

```ts
@Prop({default: "hello world", required: true}) 
myProp!: string;
```

Vue 3 - using defineProps (this does not cover defaults)
```ts
const props = defineProps<{
  myProp: {type: String, required: true }
}>();
```

Vue 3 - using defineProps with defaults
```ts
// The interface can also be used in the previous example, the ? operator makes things optional 
interface Props {
  myProp: string,
  myNonRequiredProp?: string
}

const props = withDefaults(defineProps<Props>(), {
  myProp: 'hello world'
});
```

### Migrating watchers

Vue 2 
```ts
@Watch("myData")
watchMyData() {
  this.loading = false;
}
```

Vue 3
```ts
watch(() => myData, (oldValue, newValue) => {
  loading.value = false;
})
```

