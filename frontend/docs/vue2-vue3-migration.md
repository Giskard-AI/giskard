# Vue 2 > Vue 3 migration notes

This guide is only valid in the context of Vue 2 SFC using TypeScript with `vue-property-decorator`
It is mostly made of examples, we assume the reader read Vue's docs before to understand concepts.

## Useful links

- [Vue 3's documentation](https://vuejs.org/guide/introduction.html)
- [Vue 3's TypeScript documentation](https://vuejs.org/guide/typescript/overview.html)
- 
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
class X { // ignore this class, it's just to it renders nicely
    @Prop({default: "hello world", required: true})
    myProp!: string;
}
```

Vue 3 - using defineProps (this does not cover defaults)
```ts
const props = defineProps<{
  myProp: {type: String, required: true }
}>();
```

Vue 3 - using defineProps with defaults
```ts
// The interface can also be used in the previous example, the ? operator marks as not required. 
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
class X { // ignore this class, it's just to it renders nicely
    @Watch("myData")
    watchMyData() {
        this.loading = false;
    }
}
```

Vue 3
```ts
watch(() => myData, (oldValue, newValue) => {
  loading.value = false;
})
```

### Migrating computed properties

Vue 2
```ts
class X { // ignore this class it's just so it renders nicely.
    public get myComputed(): string[] {
        return helloWorld.split(' ');
    }
}
```

Vue 3
```ts
const myComputed = computed(() => {
    return helloWorld.split(' ');
});
```

### Migrating template refs

Vue 2
```ts
// In the template, you could have ...
// <input ref="myRef" />

class X { // ignore this class, it's just to it renders nicely
    $refs!: {
        myRef: InstanceType<typeof MyType>;
    };
}
```

Vue 3
```ts
// In the template, you could have ...
// <input ref="myRef" />

const myRef = ref<MyType | null>(null);
```

The [documentation](https://vuejs.org/guide/typescript/composition-api.html#typing-template-refs) notes:
> Note that for strict type safety, it is necessary to use optional chaining or type guards when accessing el.value. This is because the initial ref value is null until the component is mounted, and it can also be set to null if the referenced element is unmounted by v-if.

