import { faCartShopping, faEdit } from "@fortawesome/free-solid-svg-icons";
import Fa from "solid-fa";
import { type Component, For } from "solid-js";

const Row: Component = () => (
  <tr class="placeholder-glow">
    <td>
      <div class="placeholder">Longer Full Name</div>
    </td>
    <td>
      <div class="placeholder">Badge</div>
    </td>
    <td>
      <div class="placeholder">Status</div>
    </td>
    <td class="text-end">
      <div class="btn-group">
        <button class="btn btn-sm placeholder">
          <Fa icon={faEdit} />
        </button>

        <button class="btn btn-sm placeholder">
          <Fa icon={faCartShopping} />
        </button>
      </div>
    </td>
  </tr>
);

export const BadgeTableLoader: Component<{ count?: number }> = (props) => {
  return (
    <For each={Array.from({ length: props.count || 1 })}>{() => <Row />}</For>
  );
};
