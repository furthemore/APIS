import { Component, For } from "solid-js";

export const BadgeTableLoader: Component<{ count?: number }> = (props) => {
  return (
    <For each={Array.from({ length: props.count || 1 })}>
      {(_, index) => <Row data-index={index()} />}
    </For>
  );
};

const Row: Component = () => {
  return (
    <tr>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Full Name</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Badge Name</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="is-skeleton">
          <div>Status</div>
        </div>
      </td>
      <td class="is-vcentered">
        <div class="buttons is-right">
          <a href="#" class="button is-small is-skeleton">
            <span class="icon">
              <i class="fas fa-edit"></i>
            </span>
          </a>

          <button class="button is-small is-skeleton">
            <span class="icon">
              <i class="fas fa-plus"></i>
            </span>
          </button>
        </div>
      </td>
    </tr>
  );
};
